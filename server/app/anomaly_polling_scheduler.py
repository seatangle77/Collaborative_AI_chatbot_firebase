import asyncio
import queue
import threading
import time
import traceback
from datetime import datetime, timezone

from server.app.anomaly_analyze import ai_analyze_anomaly_status, local_analyze
from server.app.database import db
from server.app.jpush_api import send_jpush_notification
from server.app.logger.logger_loader import logger
from server.app.websocket_routes import push_anomaly_analysis_result

# _group_id = None
_group_id = None
_users_info = None
# 120秒的间隔
_default_interval_seconds = 120
# 用户定制自己的提示间隔时间，(user_id, interval_seconds)
_user_notify_interval_seconds = {}
# 用户最后一次通知时间
_user_notify_last_time = {}

# 执行分析任务的线程
_notify_thread = None
_analyze_thread = None
_ai_analyze_thread = None
_stop_analyze = True

_ai_analyze_q = queue.Queue(1000)
_ai_analyze_result_history = []
_local_analyze_result_history = []

# 启动时间和开始分析时间，用于分析历史数据，如果_analyze_start_time设置成当前时间则从当前时间开始分析
_boot_time = datetime.now(timezone.utc)
_analyze_start_time = datetime.now(timezone.utc)

# _group_id = "cc8f1d29-7a49-4975-95dc-7ac94aefc04b"
# _stop_analyze = False
# _analyze_start_time = parse_iso_time("2025-07-10T07:02:27")
def get_analyze_start_time() -> datetime:
    return _analyze_start_time + (datetime.now(timezone.utc) - _boot_time)


def feedback_setting(group_id: str, user_id: str, click_type: str, anomaly_analysis_results_id: str = None,
    detail_type: str = None, detail_status: str = None, share_to_user_ids: list = None):
    start_time = time.time()
    logger.info(f"🖱️ [反馈点击] 收到用户{user_id}的{click_type}点击...")

    click_id = f"{group_id}_{user_id}_{int(datetime.now().timestamp())}"
    db.collection("feedback_clicks").document(click_id).set({
        "id": click_id,
        "group_id": group_id,
        "user_id": user_id,
        "click_type": click_type,
        "anomaly_analysis_results_id": anomaly_analysis_results_id,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "detail_type": detail_type,
        "detail_status": detail_status,
        "share_to_user_ids": share_to_user_ids
    })
    logger.info(f"💾 [反馈点击] 已记录点击事件到数据库")

    # Less时调整轮询周期
    if click_type == "Less":
        global _default_interval_seconds, _user_notify_interval_seconds
        old_interval = _user_notify_interval_seconds.get(user_id, _default_interval_seconds)

        if old_interval + 60 <= _default_interval_seconds * 2:
            _user_notify_interval_seconds[user_id] = old_interval + 60

        logger.info(f"📊 [反馈点击] 检测到Less点击，调整轮询间隔: {old_interval}s → {old_interval+60}s")


    logger.info(f"✅ [反馈点击] 完成！耗时{(time.time() - start_time):.2f}秒")
    return {"message": "反馈已记录"}


def start_analyze(group_id: str):
    global _group_id,_stop_analyze
    _stop_analyze = False
    _group_id = group_id

def stop_analyze(group_id: str):
    global _group_id,_stop_analyze
    _stop_analyze = True
    _group_id = group_id

def get_analyze_result():
    global _local_analyze_result_history,_ai_analyze_result_history
    return {"local":_local_analyze_result_history,"ai":_ai_analyze_result_history}

def analyze_handler():
    logger.info("🔄 [异常分析轮询] 启动分析轮询线程...")
    global _group_id, _stop_analyze, _local_analyze_result_history, _ai_analyze_q

    # 120秒的分析间隔
    interval_seconds = 120
    last_analyze_time = None
    while True:
        try:
            if _stop_analyze:
                time.sleep(1)
                continue

            if _group_id is None:
                time.sleep(1)
                logger.error("❌ [异常分析轮询] group_id未设置，无法执行分析。")
                continue


            if last_analyze_time is None:
                # 如果是第一次执行，等待interval_seconds再开始
                last_analyze_time = get_analyze_start_time()
                time.sleep(interval_seconds)
            else:
                # 检查是否需要等待。interval_seconds执行一次分析，不足时间需要等待
                elapsed = get_analyze_start_time() - last_analyze_time
                if elapsed.total_seconds() < interval_seconds:
                    time.sleep(interval_seconds - elapsed.total_seconds())

            current_time = get_analyze_start_time()

            # 本地数据分析
            chunk_data_with_local_analyze, local_analyze_result = local_analyze(_group_id, last_analyze_time, current_time)

            # 缓存本地分析结果
            if local_analyze_result:
                _local_analyze_result_history.append({current_time.strftime("%Y-%m-%dT%H:%M:%S"): local_analyze_result})
                # 只保留最近20次执行记录
                if len(_local_analyze_result_history) > 20:
                    _local_analyze_result_history = _local_analyze_result_history[-20:]


            # 写入队列，异步处理AI分析
            if chunk_data_with_local_analyze:
                _ai_analyze_q.put((_group_id, chunk_data_with_local_analyze))

            # 取本次分析的开始时间-即取数截止时间，作为下一次分析的起始时间
            last_analyze_time = current_time
        except Exception:
            logger.error('Error in analyze_handler loop: %s' % traceback.format_exc())


def ai_analyze_handler():
    logger.info("🔄 [AI异常分析] 启动分析轮询线程...")
    global  _stop_analyze, _ai_analyze_q, _ai_analyze_result_history

    while True:
        try:
            time.sleep(1)
            if _stop_analyze:
                continue

            while not _ai_analyze_q.empty():
                group_id, chunk_data_with_local_analyze = _ai_analyze_q.get()

                # 调用AI分析接口
                stage_start = time.time()
                result = None
                try:
                    result = asyncio.run(
                        ai_analyze_anomaly_status(group_id, chunk_data_with_local_analyze))
                    if not result:
                        # 无分析结果
                        continue 

                    # 缓存分析结果
                    end_time_str = chunk_data_with_local_analyze['time_range']['end']
                    _ai_analyze_result_history.append({end_time_str: result})
                    # 只保留最近20次执行记录
                    if len(_ai_analyze_result_history) > 20:
                        _ai_analyze_result_history = _ai_analyze_result_history[-20:]
                except Exception as e:
                    logger.error(f"❌ [AI异常分析] AI分析异常: {traceback.format_exc()}")
                stage2_duration = time.time() - stage_start
                logger.info(f"🤖 [AI异常分析] AI分析完成，耗时{stage2_duration:.2f}秒。结果：", str(result)[:100])

        except Exception:
            logger.error('Error in ai_analyze_handler loop: %s' % traceback.format_exc())

def notify(user):
    global _ai_analyze_result_history

    if len(_ai_analyze_result_history) < 1:
        return

    user_id = user.get("user_id"),
    user_name = user.get("name", "未知成员"),
    device_token = user.get("device_token", "")

    total_start_time = time.time()
    try:
        last_analyze_result = list(_ai_analyze_result_history[-1].values())[0]

        should_push = False
        glasses_summary = last_analyze_result.get("glasses_summary", "你当前状态需要关注")
        score = last_analyze_result.get("score")

        # 根据score的状态评分和内容相似度评分判断是否推送
        if score and isinstance(score, dict):
            state_score = score.get("state_score")
            content_similarity_score = score.get("content_similarity_score")
            if state_score is not None and content_similarity_score is not None:
                should_push = (state_score < 25 or state_score > 75) and (content_similarity_score < 50)
                logger.info(
                    f"📊 [异常分析] 状态评分：{state_score}，内容相似度评分：{content_similarity_score}，推送阈值：状态评分<25或>75，内容相似度评分<50，是否推送：{should_push}")
            else:
                should_push = True  # 如果没有评分信息，默认推送
                logger.info(f"⚠️ [异常分析] 未找到完整评分信息，默认推送")
        else:
            should_push = False  # 如果没有score信息，默认不推送
            logger.info(f"⚠️ [异常分析] 未找到评分信息，默认不推送")


        # 根据评分决定是否推送通知
        if should_push and device_token:
            # JPush 推送 - 使用眼镜版本
            send_jpush_notification(
                alert=glasses_summary,  # 直接使用眼镜版本作为推送内容
                registration_id=device_token,
                extras={
                    "type": "anomaly",
                    "title": "异常提醒",
                    "body": glasses_summary,  # 眼镜版本
                    "summary": last_analyze_result.get("summary", "暂无摘要"),
                    "suggestion": last_analyze_result.get("detail", {}).get("suggestion", ""),
                    "user_id": user_id,
                    "user_name": user_name
                }
            )
            logger.info(f"✅ [异常分析] JPush推送完成，用户 {user_name}({user_id})")
            logger.info(f"📱 [异常分析] 眼镜显示内容：{glasses_summary}")
        elif not should_push:
            logger.info(f"⏭️ [异常分析] 评分不足70分，跳过推送，用户 {user_name}({user_id})")
        else:
            logger.info(f"⚠️ [异常分析] 用户 {user_name}({user_id}) 未提供 device_token")

        # WebSocket 推送 - 向PC页面推送完整分析结果（无论评分如何都推送）
        try:
            push_anomaly_analysis_result(user_id, last_analyze_result)
        except Exception as e:
            logger.error(f"⚠️ [异常分析] WebSocket推送失败: {e}")

    except Exception as e:
        logger.info(f"❌ [AI异常通知] user_id={user_id} 导入或调用分析接口异常: {e}")

    total_duration = time.time() - total_start_time
    logger.info(f"✅ [AI异常通知] user_id={user_id} 分析完成，总耗时{total_duration:.2f}秒")


def notify_handler():
    logger.info("🔔 [AI异常通知轮询] 启动通知轮询线程...")
    global _group_id,_stop_analyze,_default_interval_seconds,_user_notify_interval_seconds,_user_notify_last_time,_users_info

    while True:
        try:
            time.sleep(1)
            if _stop_analyze:
                continue

            if _users_info is None:
                continue

            for user in _users_info:
                user_id = user.get("user_id")

                last_notify_time = _user_notify_last_time.get(user_id)
                interval_seconds = _user_notify_interval_seconds.get(user_id,_default_interval_seconds)
                if last_notify_time is None:
                    # 如果是第一次执行，初始化时间
                    _user_notify_last_time[user_id] = datetime.now(timezone.utc)
                    continue
                else:
                    # 检查是否需要等待。interval_seconds执行一次通知，不足时间继续轮询，直到超过间隔时间执行通知
                    elapsed = datetime.now(timezone.utc) - last_notify_time
                    if elapsed.total_seconds() < interval_seconds:
                        continue

                    # 执行通知
                    notify(user)

                    _user_notify_last_time[user_id] = datetime.now(timezone.utc)

        except (Exception,):
            logger.error('Error in notify_handler loop: %s' % traceback.format_exc())

def run_analyze():
    global _analyze_thread, _ai_analyze_thread, _notify_thread
    try:
        _analyze_thread = threading.Thread(target=analyze_handler, name='_analyze_thread', daemon=True)
        _analyze_thread.start()

        _ai_analyze_thread = threading.Thread(target=ai_analyze_handler, name='_ai_analyze_thread', daemon=True)
        _ai_analyze_thread.start()
        #
        # # 5s后启动通知线程，错开时间
        # time.sleep(5)
        #
        # _notify_thread = threading.Thread(target=notify_handler, name='_notify_thread', daemon=True)
        # _notify_thread.start()

    except (Exception,):
        logger.error('Error in notify_handler loop: %s' % traceback.format_exc())

if __name__ == "__main__":
    ...
    # run_analyze()
    # print(get_group_members_simple("0c90c6de-33e3-4431-b5fe-d06378111ef0"))

    # start_time = datetime.strptime("2025-07-09 02:45:00", "%Y-%m-%d %H:%M:%S")
    # end_time = datetime.strptime("2025-07-09 02:47:00", "%Y-%m-%d %H:%M:%S")
    # analyze("0c90c6de-33e3-4431-b5fe-d06378111ef0", start_time, end_time)


