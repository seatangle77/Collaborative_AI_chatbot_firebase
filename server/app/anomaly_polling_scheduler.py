import asyncio
import threading
import time
import traceback
from datetime import datetime, timezone

from server.app.anomaly_analyze import analyze_anomaly_status_new, Member
from server.app.database import db
from server.app.jpush_api import send_jpush_notification
from server.app.logger.logger_loader import logger
from server.app.websocket_routes import push_anomaly_analysis_result


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
_stop_analyze = True

_analyze_result_history = []


def get_group_members_simple(group_id: str):
    global _users_info
    try:
        start_time = time.time()
        logger.info(f"🔍 [成员查询] 开始查询group_id={group_id}的成员信息...")


        # 查询组成员关系
        query1_start = time.time()
        members_ref = db.collection("group_memberships").where("group_id", "==", group_id).stream()
        members = [doc.to_dict() for doc in members_ref]
        query1_duration = time.time() - query1_start
        logger.info(f"📋 [成员查询] 查询组成员关系完成，耗时{query1_duration:.2f}秒，找到{len(members)}个成员关系")

        user_ids = [m["user_id"] for m in members]
        users_info = []

        # 查询用户详细信息
        query2_start = time.time()
        for uid in user_ids:
            user_doc = db.collection("users_info").document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data["user_id"] = uid
                users_info.append(user_data)
        query2_duration = time.time() - query2_start
        logger.info(f"👥 [成员查询] 查询用户详细信息完成，耗时{query2_duration:.2f}秒，获取到{len(users_info)}个用户信息")

        total_duration = time.time() - start_time
        logger.info(f"✅ [成员查询] group_id={group_id}成员查询完成，总耗时{total_duration:.2f}秒")

        _users_info = users_info
        return users_info
    except Exception as e:
        logger.error(f"❌ [成员查询] group_id={group_id} 查询异常: {traceback.format_exc()}")

    return None

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


def analyze(group_id, start_time, end_time):
    global _analyze_result_history

    if group_id is None:
        logger.error("❌ [AI异常分析] group_id未设置，无法执行分析。")
        return None

    total_start_time = time.time()
    try:

        logger.info(f"🚀 [AI异常分析] group_id={group_id} 开始分析...")

        # 阶段1: 获取成员信息
        members = get_group_members_simple(group_id)
        logger.info(f"📊 [AI异常分析] 阶段1-获取成员信息完成，耗时{(time.time() - total_start_time):.2f}秒")

        member_objs = [Member(id=m.get("user_id"), name=m.get("name", "未知成员")) for m in members]

        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        logger.info(f"🕐 [AI异常分析] 分析时间窗口: {start_time_str} ~ {end_time_str}")


        # 阶段2: 调用分析接口
        stage2_start = time.time()
        result = None
        try:
            result = asyncio.run(analyze_anomaly_status_new(group_id,1,start_time_str,end_time_str,member_objs))

            # 缓存分析结果
            _analyze_result_history.append((end_time, result))
            # 只保留最近10次执行记录
            if len(_analyze_result_history) > 10:
                _analyze_result_history = _analyze_result_history[-10:]
        except Exception as e:
            logger.error(f"❌ [AI异常分析] 阶段2-AI分析异常: {traceback.format_exc()}")
        stage2_duration = time.time() - stage2_start
        logger.info(f"🤖 [AI异常分析] 阶段2-AI分析完成，耗时{stage2_duration:.2f}秒。结果：", str(result)[:100])
    except Exception as e:
        logger.error(f"❌ [AI异常分析] group_id={group_id} 导入或调用分析接口异常: {traceback.format_exc()}")

    total_duration = time.time() - total_start_time
    logger.info(f"✅ [AI异常分析] group_id={group_id} 分析完成，总耗时{total_duration:.2f}秒")


def start_analyze(group_id: str):
    global _group_id,_stop_analyze
    _stop_analyze = False
    _group_id = group_id

def stop_analyze(group_id: str):
    global _group_id,_stop_analyze
    _stop_analyze = True
    _group_id = group_id

def analyze_handler():
    logger.info("🔄 [AI异常分析轮询] 启动分析轮询线程...")
    global _group_id, _stop_analyze

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
                logger.error("❌ [AI异常分析轮询] group_id未设置，无法执行分析。")
                continue


            if last_analyze_time is None:
                # 如果是第一次执行，等待interval_seconds再开始
                last_analyze_time = datetime.now(timezone.utc)
                time.sleep(interval_seconds)
            else:
                # 检查是否需要等待。interval_seconds执行一次分析，不足时间需要等待
                elapsed = datetime.now(timezone.utc) - last_analyze_time
                if elapsed.total_seconds() < interval_seconds:
                    time.sleep(interval_seconds - elapsed.total_seconds())

            current_time = datetime.now(timezone.utc)

            # 这里是分析逻辑
            analyze(_group_id, last_analyze_time, current_time)

            # 取本次分析的开始时间-即取数截止时间，作为下一次分析的起始时间
            last_analyze_time = current_time
        except Exception:
            logger.error('Error in analyze_handler loop: %s' % traceback.format_exc())


def notify(user):
    global _analyze_result_history

    if len(_analyze_result_history) < 1:
        return

    user_id = user.get("user_id"),
    user_name = user.get("name", "未知成员"),
    device_token = user.get("device_token", "")

    total_start_time = time.time()
    try:
        last_analyze_result = _analyze_result_history[-1][1]

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
    global _analyze_thread, _notify_thread
    try:
        _analyze_thread = threading.Thread(target=analyze_handler, name='_analyze_thread', daemon=True)
        _analyze_thread.start()

        # 5s后启动通知线程，错开时间
        time.sleep(5)

        _notify_thread = threading.Thread(target=notify_handler, name='_notify_thread', daemon=True)
        _notify_thread.start()

    except (Exception,):
        logger.error('Error in notify_handler loop: %s' % traceback.format_exc())

if __name__ == "__main__":
    # run_analyze()
    print(get_group_members_simple("0c90c6de-33e3-4431-b5fe-d06378111ef0"))
