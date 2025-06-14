from app.database import db
import os, json
from datetime import datetime
from datetime import timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

def extract_chunk_data_anomaly(round_index: int, start_time: str, end_time: str, group_id: str, member_list: list) -> dict:
    """
    获取当前 chunk 内所有用户的行为数据，准备送入 GPT 处理。
    返回结构包含每位用户的行为/标签数据。
    """
    def parse_firestore_time(chinese_str):
        try:
            return datetime.strptime(chinese_str, "%Y年%m月%d日 UTC+8 %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=8)))
        except Exception:
            return None

    # Ensure start_time_dt and end_time_dt are timezone-aware, set to UTC+8
    start_time_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone(timedelta(hours=8)))
    end_time_dt = datetime.fromisoformat(end_time).replace(tzinfo=timezone(timedelta(hours=8)))

    user_ids = [m["user_id"] for m in member_list]
    # print("📋 活跃用户 user_ids:", user_ids)
    # print("🧪 extract_chunk_data inputs:", {"group_id": group_id, "start_time": start_time, "end_time": end_time})

    def filter_time_range(item_start, item_end=None):
        # 判断时间字符串是否在 start_time 和 end_time 范围内
        # item_end 如果为空，则只判断 item_start 是否在范围内
        return (start_time <= item_start <= end_time) if item_end is None else (item_start <= end_time and item_end >= start_time)

    # 查询 speech_transcripts
    speech_transcripts = [doc.to_dict() for doc in db.collection("speech_transcripts").where(filter=FieldFilter("group_id", "==", group_id)).stream()]
    speech_transcripts = [s for s in speech_transcripts if filter_time_range(s.get("start"), s.get("end"))]
    # 按 user_id 统计发言次数
    from collections import Counter
    speech_counts = Counter(s["user_id"] for s in speech_transcripts if s.get("user_id"))
    for m in member_list:
        m["speech_count"] = speech_counts.get(m["user_id"], 0)
    #print(f"🎯 speech_transcripts count: {len(speech_transcripts)}")

    # 查询 note_edit_history
    def parse_firestore_timestamp(ts):
        if isinstance(ts, dict) and "_seconds" in ts:
            return datetime.fromtimestamp(
                ts["_seconds"] + ts.get("_nanoseconds", 0) / 1e9
            ).replace(tzinfo=timezone(timedelta(hours=8)))
        return None
    note_edit_history = []
    if member_list:
        for m in member_list:
            uid = m["user_id"]
            query = db.collection("note_edit_history").where(filter=FieldFilter("userId", "==", uid)).stream()
            note_edit_history.extend([doc.to_dict() for doc in query])

    filtered_note_edit_history = []
    for e in note_edit_history:
        ts = parse_firestore_timestamp(e.get("timestamp"))

        
        if ts and start_time_dt <= ts <= end_time_dt:
            filtered_note_edit_history.append(e)

    note_edit_history = filtered_note_edit_history
    #print(f"📝 note_edit_history count: {len(note_edit_history)}")

    # 查询 pageBehaviorLogs
    pageBehaviorLogs = []
    all_logs = db.collection("pageBehaviorLogs").stream()
    count_all = 0
    count_group_matched = 0
    for doc in all_logs:
        count_all += 1
        data = doc.to_dict()
        user_info = data.get("behaviorData", {}).get("user", {})
        if user_info.get("group_id") == group_id:
            count_group_matched += 1
            pageBehaviorLogs.append(data)
    filtered_logs = []
    for b in pageBehaviorLogs:
        ws = parse_firestore_time(b.get("windowStart"))
        we = parse_firestore_time(b.get("windowEnd"))
        if ws and we and start_time_dt <= ws <= end_time_dt:
            filtered_logs.append(b)
    pageBehaviorLogs = filtered_logs
    #print(f"📝 pageBehaviorLogs: {pageBehaviorLogs}")


    # 查询 note_contents，先根据 userId 再本地筛选 updatedAt
    note_contents_all = []
    if member_list:
        uid = member_list[0]["user_id"]
        query = db.collection("note_contents")\
            .where(filter=FieldFilter("userId", "==", uid))\
            .stream()
        note_contents_all.extend([doc.to_dict() for doc in query])

    note_contents = []
    for n in note_contents_all:
        ts_str = n.get("updatedAt", "")
        ts = parse_firestore_time(ts_str)
        if ts and start_time_dt <= ts <= end_time_dt:
            note_contents.append(n)
    #print(f"📝 note_contents: {note_contents}")


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
        "speech_counts": speech_counts
    }

    from uuid import uuid4
    os.makedirs("debug_anomaly_outputs", exist_ok=True)
    debug_file_path = f"debug_anomaly_outputs/chunk_data_{uuid4().hex}.json"
    with open(debug_file_path, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, ensure_ascii=False, indent=2)

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