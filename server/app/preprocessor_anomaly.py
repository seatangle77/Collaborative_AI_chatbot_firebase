from app.database import db
import os, json
from datetime import datetime
from datetime import timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter
import time

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

def extract_chunk_data_anomaly(round_index: int, start_time: str, end_time: str, group_id: str, member_list: list, current_user: dict) -> dict:
    """
    获取当前 chunk 内所有用户的行为数据，准备送入 GPT 处理。
    返回结构包含每位用户的行为/标签数据。
    """
    total_start_time = time.time()
    print(f"🔍 [数据预处理] 开始提取group_id={group_id}的数据，时间范围：{start_time} ~ {end_time}")
    
    # 统一解析为datetime对象
    start_time_dt = parse_iso_time(start_time)
    end_time_dt = parse_iso_time(end_time)

    user_ids = [m["user_id"] for m in member_list]
    print(f"📋 [数据预处理] 活跃用户数量：{len(user_ids)}")

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
    print(f"🎤 [数据预处理] 查询1-speech_transcripts完成，耗时{query1_duration:.2f}秒，找到{len(speech_transcripts)}条记录")

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
    print(f"📝 [数据预处理] 查询2-note_edit_history完成，耗时{query2_duration:.2f}秒，找到{len(note_edit_history)}条记录")

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
    query3_duration = time.time() - query3_start
    print(f"🖥️ [数据预处理] 查询3-pageBehaviorLogs完成，耗时{query3_duration:.2f}秒，找到{len(pageBehaviorLogs)}条记录")

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
    print(f"📄 [数据预处理] 查询4-note_contents完成，耗时{query4_duration:.2f}秒，找到{len(note_contents)}条记录")

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
        "speech_durations": dict(speech_durations),
        "current_user": current_user
    }

    # 查询5: anomaly_analysis_results历史
    query5_start = time.time()
    try:
        # 计算时间范围：从start_time往前半小时到start_time
        history_start_time = start_time_dt - timedelta(minutes=30)
        history_start_time_str = history_start_time.isoformat()
        
        results = db.collection("anomaly_analysis_results") \
            .where(filter=FieldFilter("group_id", "==", group_id)) \
            .where(filter=FieldFilter("current_user.user_id", "==", current_user["user_id"])) \
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
        print(f"📚 [数据预处理] 查询5-anomaly_analysis_results历史完成，耗时{query5_duration:.2f}秒，找到{len(anomaly_history)}条历史记录")
    except Exception as e:
        query5_duration = time.time() - query5_start
        print(f"❌ [数据预处理] 查询5-anomaly_analysis_results历史失败，耗时{query5_duration:.2f}秒：{e}")
        chunk_data["anomaly_history"] = None

    # 保存调试文件
    debug_start = time.time()
    from uuid import uuid4
    os.makedirs("debug_anomaly_outputs", exist_ok=True)
    debug_file_path = f"debug_anomaly_outputs/chunk_data_{uuid4().hex}.json"
    with open(debug_file_path, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)
    debug_duration = time.time() - debug_start
    print(f"💾 [数据预处理] 保存调试文件完成，耗时{debug_duration:.2f}秒")

    total_duration = time.time() - total_start_time
    print(f"✅ [数据预处理] group_id={group_id}数据提取完成，总耗时{total_duration:.2f}秒")

    return chunk_data


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
    import sys
    import os
    # 添加当前目录到Python路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    group_id = "fcdf6669-745a-44e0-88b9-5c361e78d31e"
    start_time = "2025-07-06T05:29:28"
    end_time = "2025-07-06T05:37:28"
    start_time_dt = parse_iso_time(start_time)
    end_time_dt = parse_iso_time(end_time)
    member_list = [{"user_id": "HGa3L2y3eSf7KXYQs793vLWnQRu2"}, {"user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2"}]

