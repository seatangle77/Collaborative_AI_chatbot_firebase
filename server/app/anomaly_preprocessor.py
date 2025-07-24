import copy
from collections import defaultdict
from typing import Tuple

from server.app.database import db
import os, json
from datetime import datetime
from datetime import timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter
import time

from server.app.logger.logger_loader import logger


def parse_iso_time(iso_str):
    if not iso_str:
        return None
    if isinstance(iso_str, dict) and "_seconds" in iso_str:
        # Firestore timestamp dict
        return datetime.fromtimestamp(
            iso_str["_seconds"] + iso_str.get("_nanoseconds", 0) / 1e9,
            tz=timezone.utc
        )
    if iso_str.endswith("Z"):
        iso_str = iso_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso_str)
        # 关键处理：无时区标识时设为东八区
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=0)))
        return dt
    except Exception:
        return None

def merge_tab_behavior_logs(actions):
    """
    连续同类型操作合并，记录开始时间、结束时间、操作次数、首尾位置等。
    mousemove: 合并连续，保留首尾位置和时间。
    scroll: 合并连续，保留首尾时间、最大/最小maxDepth。
    click: 合并连续，保留首尾位置和时间、次数。
    其他类型保持原样。
    """
    if not actions:
        return []
    merged = []
    i = 0
    n = len(actions)
    while i < n:
        curr = actions[i]
        curr_type = curr.get('type')
        curr_tabid = curr.get('tabId')
        start_time = curr.get('timestamp')
        end_time = curr.get('timestamp')
        count = 1
        positions = []
        maxDepths = []
        if curr_type == 'mousemove' and 'position' in curr:
            positions.append(curr['position'])
        if curr_type == 'scroll' and 'maxDepth' in curr:
            maxDepths.append(curr['maxDepth'])
        if curr_type == 'click' and 'position' in curr:
            positions.append(curr['position'])

        # 向后查找连续的同类型操作
        j = i + 1
        while j < n and actions[j].get('type') == curr_type and actions[j].get('tabId') == curr_tabid:
            end_time = actions[j].get('timestamp')
            count += 1
            if curr_type == 'mousemove' and 'position' in actions[j]:
                positions.append(actions[j]['position'])
            if curr_type == 'scroll' and 'maxDepth' in actions[j]:
                maxDepths.append(actions[j]['maxDepth'])
            if curr_type == 'click' and 'position' in actions[j]:
                positions.append(actions[j]['position'])
            j += 1

        merged_item = {
            'type': curr_type,
            'startTime': start_time,
            'endTime': end_time,
            'action_count': count
        }
        if curr_type == 'mousemove' and positions:
            merged_item['startPosition'] = positions[0]
            merged_item['endPosition'] = positions[-1]
        if curr_type == 'scroll' and maxDepths:
            merged_item['minDepth'] = min(maxDepths)
            merged_item['maxDepth'] = max(maxDepths)
        if curr_type == 'click' and positions:
            merged_item['position'] = positions[0]
        merged.append(merged_item)
        i = j
    return merged

def compress_page_behavior_logs(pageBehaviorLogs):
    """
    对 pageBehaviorLogs 进行压缩
    """
    # 1. 按 user 合并日志
    user_logs = defaultdict(list)
    users = {}
    for log in pageBehaviorLogs:
        user = log.get('behaviorData', {}).get('user', {})
        user_name = user.get('userName')
        if user_name:
            user_logs[user_name].append(log)
            users[user_name]=user

    # 2. 按 windowStart 排序，合并连续的时间窗口的操作
    compressed = {}
    for user_name, logs in user_logs.items():
        logs.sort(key=lambda x: parse_iso_time(x.get('windowStart')) or datetime.min)
        merged_windows = {}
        for log in logs:
            if 'windowStart' not in merged_windows:
                merged_windows['windowStart'] = log.get('windowStart')
            merged_windows['windowEnd'] = log.get('windowEnd')
            if 'tabHistory' not in merged_windows:
                merged_windows['tabHistory'] = []

            # 合并 tabHistory 合并去重
            tab_hist_map = {t['tabId']: t for t in merged_windows['tabHistory']}
            tabHistory = log.get('behaviorData', {}).get('tabHistory', [])
            for t in tabHistory:
                if t['tabId'] not in tab_hist_map:
                    tab_hist_map[t['tabId']] = t
                    del tab_hist_map[t['tabId']]['active']

            # 合并 tabBehaviorLogs 到具体 tab
            tabBehaviorLogs = log.get('behaviorData', {}).get('tabBehaviorLogs', [])
            for action in tabBehaviorLogs:
                tabid = action["tabId"]
                if tabid not in tab_hist_map:
                    # 如果 tabId 不在 tabHistory 中，跳过
                    continue
                else:
                    if 'tabBehaviorLogs' not in tab_hist_map[tabid]:
                        tab_hist_map[tabid]['tabBehaviorLogs'] = []
                    tab_hist_map[tabid]['tabBehaviorLogs'].append(copy.deepcopy(action))

            merged_windows['tabHistory'] = list(tab_hist_map.values())


        # 只保留有活动的tab，将连续的活动进行合并
        active_tabHistory = []
        for t in merged_windows['tabHistory']:
            # 过滤掉没有 tabBehaviorLogs 的 tabHistory
            if 'tabBehaviorLogs' in t and t['tabBehaviorLogs']:
                # 对每个 tabHistory 的 tabBehaviorLogs 进行合并
                t['tabBehaviorLogs'] = merge_tab_behavior_logs(t['tabBehaviorLogs'])
                active_tabHistory.append(t)
        merged_windows['tabHistory'] = active_tabHistory

        compressed[user_name] = {
            'user': users[user_name],
            'windowRanges': {'windowStart':merged_windows['windowStart'],'windowEnd':merged_windows['windowEnd']},
            'tabHistory': merged_windows['tabHistory']
        }
    return compressed

def extract_chunk_data_anomaly(round_index: int, start_time: str, end_time: str, group_id: str, member_list: list) -> Tuple[dict,int]:
    """
    获取当前 chunk 内所有用户的行为数据，准备送入 GPT 处理。
    返回结构包含每位用户的行为/标签数据。
    """
    total_start_time = time.time()
    logger.info(f"🔍 [数据预处理] 开始提取group_id={group_id}的数据，时间范围：{start_time} ~ {end_time}")
    
    # 统一解析为datetime对象
    start_time_dt = parse_iso_time(start_time)
    end_time_dt = parse_iso_time(end_time)

    user_ids = [m["user_id"] for m in member_list]
    logger.info(f"📋 [数据预处理] 活跃用户数量：{len(user_ids)}")

    ########################################
    # 查询1: speech_transcripts
    query1_start = time.time()
    # 查询1.1: start时间在范围内的记录
    speech_transcripts_start = [doc.to_dict() for doc in db.collection("speech_transcripts")
        .where(filter=FieldFilter("group_id", "==", group_id))
        .where(filter=FieldFilter("start", ">=", start_time))
        .where(filter=FieldFilter("start", "<=", end_time))
        .stream()]
    
    # 查询1.2: end时间在范围内的记录
    speech_transcripts_end = [doc.to_dict() for doc in db.collection("speech_transcripts")
        .where(filter=FieldFilter("group_id", "==", group_id))
        .where(filter=FieldFilter("end", ">=", start_time))
        .where(filter=FieldFilter("end", "<=", end_time))
        .stream()]
    
    # 合并两个查询结果并去重
    speech_transcripts = speech_transcripts_start + speech_transcripts_end
    # 使用transcript_id去重
    seen_ids = set()
    unique_speech_transcripts = []
    for transcript in speech_transcripts:
        transcript_id = transcript.get("transcript_id")
        if transcript_id not in seen_ids:
            seen_ids.add(transcript_id)
            unique_speech_transcripts.append(transcript)
    
    speech_transcripts = unique_speech_transcripts
    # 按 user_id 统计发言次数和时长
    from collections import Counter, defaultdict
    speech_counts = Counter(s["user_id"] for s in speech_transcripts if s.get("user_id"))
    speech_durations = defaultdict(float)
    
    for s in speech_transcripts:
        if s.get("user_id") and s.get("duration"):
            speech_durations[s["user_id"]] += s["duration"]
    
    for m in member_list:
        m["speech_count"] = speech_counts.get(m["user_id"], 0)
        m["speech_duration"] = round(speech_durations.get(m["user_id"], 0), 2)
    query1_duration = time.time() - query1_start
    logger.info(f"🎤 [数据预处理] 查询1-speech_transcripts完成，耗时{query1_duration:.2f}秒，找到{len(speech_transcripts)}条记录")

    ########################################
    # 查询2: note_edit_history
    query2_start = time.time()
    note_edit_history = []
    if member_list:
        for m in member_list:
            uid = m["user_id"]
            # 直接在查询中添加时间过滤条件
            query = db.collection("note_edit_history")\
                .where(filter=FieldFilter("userId", "==", uid))\
                .where(filter=FieldFilter("updatedAt", ">=", start_time))\
                .where(filter=FieldFilter("updatedAt", "<=", end_time))\
                .stream()
            note_edit_history.extend([doc.to_dict() for doc in query])
    
    query2_duration = time.time() - query2_start
    logger.info(f"📝 [数据预处理] 查询2-note_edit_history完成，耗时{query2_duration:.2f}秒，找到{len(note_edit_history)}条记录")

    ########################################
    # 查询3: pageBehaviorLogs
    query3_start = time.time()
    pageBehaviorLogs = []
    
    # 查询3.1: group_id匹配且windowStart在时间范围内的记录
    logs_start = []
    query_start = db.collection("pageBehaviorLogs")\
        .where(filter=FieldFilter("behaviorData.user.group_id", "==", group_id))\
        .where(filter=FieldFilter("windowStart", ">=", start_time))\
        .where(filter=FieldFilter("windowStart", "<=", end_time))\
        .stream()
    for doc in query_start:
        logs_start.append(doc.to_dict())
    
    # 查询3.2: group_id匹配且windowEnd在时间范围内的记录
    logs_end = []
    query_end = db.collection("pageBehaviorLogs")\
        .where(filter=FieldFilter("behaviorData.user.group_id", "==", group_id))\
        .where(filter=FieldFilter("windowEnd", ">=", start_time))\
        .where(filter=FieldFilter("windowEnd", "<=", end_time))\
        .stream()
    for doc in query_end:
        logs_end.append(doc.to_dict())
    
    # 合并两个查询结果并去重
    pageBehaviorLogs = logs_start + logs_end
    # 使用某个唯一标识去重
    seen_ids = set()
    unique_logs = []
    for log in pageBehaviorLogs:
        log_id = log.get("id") or log.get("_id") or str(log)
        if log_id not in seen_ids:
            seen_ids.add(log_id)
            unique_logs.append(log)
    
    pageBehaviorLogs = unique_logs
    # 压缩 pageBehaviorLogs
    pageBehaviorLogs = compress_page_behavior_logs(pageBehaviorLogs)
    query3_duration = time.time() - query3_start
    logger.info(f"🖥️ [数据预处理] 查询3-pageBehaviorLogs完成，耗时{query3_duration:.2f}秒，找到{len(unique_logs)}条记录")

    ########################################
    # 查询4: note_contents
    query4_start = time.time()
    note_contents = []
    if member_list:
        uid = member_list[0]["user_id"]
        # 直接在查询中添加时间过滤条件
        query = db.collection("note_contents")\
            .where(filter=FieldFilter("userId", "==", uid))\
            .where(filter=FieldFilter("updatedAt", ">=", start_time))\
            .where(filter=FieldFilter("updatedAt", "<=", end_time))\
            .stream()
        note_contents.extend([doc.to_dict() for doc in query])

    query4_duration = time.time() - query4_start
    logger.info(f"📄 [数据预处理] 查询4-note_contents完成，耗时{query4_duration:.2f}秒，找到{len(note_contents)}条记录")

    chunk_data = {
        "time_range": {
            "start": start_time,
            "end": end_time
        },
        "group_id": group_id,
        "users": member_list,
        "raw_tables": {
            "speech_transcripts": speech_transcripts,
            "note_edit_history": note_edit_history,
            "pageBehaviorLogs": pageBehaviorLogs,
            "unique_note_contents": note_contents
        },
        "speech_counts": speech_counts,
        "speech_durations": dict(speech_durations)
    }

    ########################################
    # 查询5: anomaly_analysis_results历史
    query5_start = time.time()
    try:
        # 计算时间范围：从start_time往前半小时到start_time
        history_start_time = start_time_dt - timedelta(minutes=30)
        history_start_time_str = history_start_time.isoformat()
        
        results = db.collection("anomaly_analysis_results") \
            .where(filter=FieldFilter("group_id", "==", group_id)) \
            .where(filter=FieldFilter("created_at", ">=", history_start_time_str)) \
            .where(filter=FieldFilter("created_at", "<=", start_time)) \
            .order_by("created_at", direction="DESCENDING") \
            .limit(2) \
            .stream()
        history = [doc.to_dict() for doc in results]
        anomaly_history = []
        for h in history:
            anomaly_history.append({
                "detail": h.get("detail"),
                "glasses_summary": h.get("glasses_summary"),
                "summary": h.get("summary"),
                "user_data_summary": h.get("user_data_summary"),
                "start_time": h.get("start_time"),
                "end_time": h.get("end_time")
            })
        if len(anomaly_history) == 0:
            chunk_data["anomaly_history"] = None
        else:
            chunk_data["anomaly_history"] = anomaly_history
        query5_duration = time.time() - query5_start
        logger.info(f"📚 [数据预处理] 查询5-anomaly_analysis_results历史完成，耗时{query5_duration:.2f}秒，找到{len(anomaly_history)}条历史记录")
    except Exception as e:
        query5_duration = time.time() - query5_start
        logger.error(f"❌ [数据预处理] 查询5-anomaly_analysis_results历史失败，耗时{query5_duration:.2f}秒：{e}")
        chunk_data["anomaly_history"] = None

    # 保存调试文件
    debug_start = time.time()
    from uuid import uuid4
    os.makedirs("debug_anomaly_outputs", exist_ok=True)
    debug_file_path = f"debug_anomaly_outputs/chunk_data_{uuid4().hex}.json"
    with open(debug_file_path, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)
    debug_duration = time.time() - debug_start
    logger.info(f"💾 [数据预处理] 保存调试文件完成，耗时{debug_duration:.2f}秒")

    total_duration = time.time() - total_start_time
    logger.info(f"✅ [数据预处理] group_id={group_id}数据提取完成，总耗时{total_duration:.2f}秒")

    # 用户活动记录的增量数量
    increment = len(speech_transcripts) + len(note_edit_history) + len(pageBehaviorLogs) + len(note_contents)

    return chunk_data, increment


def build_cognitive_anomaly_input(chunk_data: dict) -> dict:
    """
    构建用于认知分析任务的 GPT 输入结构。
    """
    return {
        "group_id": chunk_data["group_id"],
        "time_range": chunk_data["time_range"],
        "users": chunk_data["users"],
        "speech_transcripts": chunk_data["raw_tables"]["speech_transcripts"],
        "unique_note_contents": chunk_data["raw_tables"]["unique_note_contents"]
    }


def build_behavior_anomaly_input(chunk_data: dict) -> dict:
    """
    构建用于行为分析任务的 GPT 输入结构。
    """
    return {
        "group_id": chunk_data["group_id"],
        "time_range": chunk_data["time_range"],
        "users": chunk_data["users"],
        "note_edit_history": chunk_data["raw_tables"]["note_edit_history"],
        "pageBehaviorLogs": chunk_data["raw_tables"]["pageBehaviorLogs"],
        "speech_counts": chunk_data.get("speech_counts", {})
    }


def build_attention_anomaly_input(chunk_data: dict) -> dict:
    """
    构建用于注意力分析任务的 GPT 输入结构。
    """
    return {
        "group_id": chunk_data["group_id"],
        "time_range": chunk_data["time_range"],
        "users": chunk_data["users"],
        "note_edit_history": chunk_data["raw_tables"]["note_edit_history"],
        "pageBehaviorLogs": chunk_data["raw_tables"]["pageBehaviorLogs"],
        "speech_transcripts": chunk_data["raw_tables"]["speech_transcripts"],
    }

def build_anomaly_history_input(chunk_data: dict) -> dict:
    """
    构建用于异常历史分析的输入结构。
    """
    return {
        "current_user": chunk_data.get("current_user"),
        "anomaly_history": chunk_data.get("anomaly_history")
    }



if __name__ == '__main__':
    ...

    input_file = "../debug_anomaly_outputs/chunk_data_18b4c9cf636e45e8829738b96f4f53bb.json"
    output_file = "../debug_anomaly_outputs/chunk_data_18b4c9cf636e45e8829738b96f4f53bb_merge.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        pageBehaviorLogs = json.load(f)
    compressed = compress_page_behavior_logs(pageBehaviorLogs["raw_tables"]["pageBehaviorLogs"])
    pageBehaviorLogs["raw_tables"]["pageBehaviorLogs"] = compressed
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pageBehaviorLogs, f, ensure_ascii=False, indent=2)
    print(f"压缩完成，结果已保存到 {output_file}")