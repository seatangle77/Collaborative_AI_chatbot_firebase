import queue
import threading
import time
import traceback
from datetime import datetime, timezone

from server.app.anomaly_analyze import ai_analyze_anomaly_status, local_analyze
from server.app.anomaly_preprocessor import parse_iso_time
from server.app.logger.logger_loader import logger

_group_id = None
_users_info = None
# 120秒的间隔
_default_interval_seconds = 120

# 是否停止分析
_stop_analyze = True

# 执行分析任务的线程
_analyze_thread = None
_ai_analyze_thread = None

_ai_analyze_q = queue.Queue(1000)

# 启动时间和开始分析时间，用于分析历史数据，如果_analyze_start_time设置成当前时间则从当前时间开始分析
_boot_time = datetime.now(timezone.utc)
_analyze_start_time = datetime.now(timezone.utc)

# _group_id = "cc8f1d29-7a49-4975-95dc-7ac94aefc04b"
# _stop_analyze = False
# _analyze_start_time = parse_iso_time("2025-07-10T07:02:27")
def get_analyze_start_time() -> datetime:
    return _analyze_start_time + (datetime.now(timezone.utc) - _boot_time)

def clear_cache():
    global _group_id, _users_info, _ai_analyze_q, _ai_analyze_result_histor
    _group_id = None
    _users_info = None
    _ai_analyze_q = queue.Queue(1000)


def start_analyze(group_id: str):
    clear_cache()

    global _group_id,_stop_analyze
    _stop_analyze = False
    _group_id = group_id

def stop_analyze(group_id: str):
    global _stop_analyze
    _stop_analyze = True

    clear_cache()

def analyze_handler():
    logger.info("🔄 [异常分析轮询] 启动分析轮询线程...")
    global _group_id, _stop_analyze, _ai_analyze_q

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

            # 写入队列，异步处理AI分析
            if chunk_data_with_local_analyze:
                _ai_analyze_q.put((_group_id, chunk_data_with_local_analyze))

            # 取本次分析的开始时间-即取数截止时间，作为下一次分析的起始时间
            last_analyze_time = current_time
        except Exception:
            logger.error('Error in analyze_handler loop: %s' % traceback.format_exc())


def ai_analyze_handler():
    logger.info("🔄 [AI异常分析] 启动分析轮询线程...")
    global  _stop_analyze, _ai_analyze_q

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
                    result = ai_analyze_anomaly_status(group_id, chunk_data_with_local_analyze)
                    if not result:
                        # 无分析结果
                        continue 

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


