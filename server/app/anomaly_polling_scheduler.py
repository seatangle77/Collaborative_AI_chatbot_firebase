import asyncio
import queue
import threading
import time
import traceback
from datetime import datetime, timezone, timedelta

from server.app.anomaly_analyze import ai_analyze_anomaly_status, local_analyze
from server.app.anomaly_preprocessor import parse_iso_time
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

# 是否停止分析
_stop_analyze = True

# 执行分析任务的线程
_analyze_thread = None
_ai_analyze_thread = None

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

def clear_cache():
    global _group_id, _users_info, _user_notify_interval_seconds, _user_notify_last_time,_ai_analyze_q, _ai_analyze_result_histor, _local_analyze_result_history
    _group_id = None
    _users_info = None
    _user_notify_interval_seconds = {}
    _user_notify_last_time = {}

    _ai_analyze_q = queue.Queue(1000)
    _ai_analyze_result_history = []
    _local_analyze_result_history = []

def feedback_setting(group_id: str, user_id: str, click_type: str, anomaly_analysis_results_id: str = None,
    detail_type: str = None, detail_status: str = None, share_to_user_ids: list = None):
    start_time = time.time()
    logger.info(f"🖱️ [反馈点击] 收到用户{user_id}的{click_type}点击...")

    # Less\More 时调整轮询周期
    global _default_interval_seconds, _user_notify_interval_seconds
    if click_type == "Less":
        old_interval = _user_notify_interval_seconds.get(user_id, _default_interval_seconds)

        if old_interval + 60 <= _default_interval_seconds * 2:
            _user_notify_interval_seconds[user_id] = old_interval + 60

        logger.info(f"📊 [反馈点击] 检测到Less点击，调整轮询间隔: {old_interval}s → {_user_notify_interval_seconds.get(user_id, _default_interval_seconds)}s")
    elif click_type == "More":
        old_interval = _user_notify_interval_seconds.get(user_id, _default_interval_seconds)

        if old_interval - 60 >= _default_interval_seconds:
            _user_notify_interval_seconds[user_id] = old_interval - 60

        logger.info(f"📊 [反馈点击] 检测到More点击，调整轮询间隔: {old_interval}s → {_user_notify_interval_seconds.get(user_id, _default_interval_seconds)}s")

    click_id = f"{group_id}_{user_id}_{int(datetime.now().timestamp())}"
    feedback_setting = {
        "id": click_id,
        "group_id": group_id,
        "user_id": user_id,
        "click_type": click_type,
        "anomaly_analysis_results_id": anomaly_analysis_results_id,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "detail_type": detail_type,
        "detail_status": detail_status,
        "share_to_user_ids": share_to_user_ids,
        "interval_seconds": _user_notify_interval_seconds.get(user_id, _default_interval_seconds),
    }
    db.collection("feedback_clicks").document(click_id).set(feedback_setting)

    logger.info(f"✅ [反馈点击] 完成！耗时{(time.time() - start_time):.2f}秒")
    return {"message": "反馈已记录", "feedback_setting": feedback_setting}


def start_analyze(group_id: str):
    clear_cache()

    global _group_id,_stop_analyze
    _stop_analyze = False
    _group_id = group_id

def stop_analyze(group_id: str):
    global _stop_analyze
    _stop_analyze = True

    clear_cache()

def get_local_analyze_result():
    global _local_analyze_result_history
    return _local_analyze_result_history

def get_ai_analyze_result():
    global _ai_analyze_result_history
    return _ai_analyze_result_history

def get_next_notify_ai_analyze_result():
    global _ai_analyze_result_history, _user_notify_last_time, _user_notify_interval_seconds, _default_interval_seconds
    if len(_ai_analyze_result_history) > 0:
        last_ai_analyze_result = _ai_analyze_result_history[-1]
        last_ai_analyze_time = list(last_ai_analyze_result.keys())[0]

        last_ai_analyze_content = last_ai_analyze_result.get(last_ai_analyze_time)

        user_ids = list(last_ai_analyze_content.keys())
        for user_id in user_ids:
            last_notify_time = _user_notify_last_time.get(user_id)
            interval_seconds = _user_notify_interval_seconds.get(user_id, _default_interval_seconds)
            if last_notify_time is None:
                # 如果是第一次执行，用AI分析结果的时间作为下次通知时间
                next_notify_time = parse_iso_time(last_ai_analyze_time)
            else:
                # 上一次通知时间+间隔时间作为下一次通知时间
                next_notify_time = last_notify_time + timedelta(seconds=interval_seconds)

            last_ai_analyze_content.get(user_id, {}).update({"next_notify_time": next_notify_time.isoformat()})
    return

def set_notify_time(user_id: str):
    global _user_notify_last_time
    _user_notify_last_time[user_id] = datetime.now(timezone.utc)

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


def run_analyze():
    global _analyze_thread, _ai_analyze_thread, _notify_thread
    try:
        _analyze_thread = threading.Thread(target=analyze_handler, name='_analyze_thread', daemon=True)
        _analyze_thread.start()

        _ai_analyze_thread = threading.Thread(target=ai_analyze_handler, name='_ai_analyze_thread', daemon=True)
        _ai_analyze_thread.start()
    except (Exception,):
        logger.error('Error in notify_handler loop: %s' % traceback.format_exc())

if __name__ == "__main__":
    ...
    # run_analyze()
    # print(get_group_members_simple("0c90c6de-33e3-4431-b5fe-d06378111ef0"))

    # start_time = datetime.strptime("2025-07-09 02:45:00", "%Y-%m-%d %H:%M:%S")
    # end_time = datetime.strptime("2025-07-09 02:47:00", "%Y-%m-%d %H:%M:%S")
    # analyze("0c90c6de-33e3-4431-b5fe-d06378111ef0", start_time, end_time)


