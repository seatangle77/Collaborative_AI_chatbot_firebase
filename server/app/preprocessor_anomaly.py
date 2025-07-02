from app.database import db
import os, json
from datetime import datetime
from datetime import timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

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
        return datetime.fromisoformat(iso_str)
    except Exception:
        return None

def extract_chunk_data_anomaly(round_index: int, start_time: str, end_time: str, group_id: str, member_list: list, current_user: dict) -> dict:
    """
    获取当前 chunk 内所有用户的行为数据，准备送入 GPT 处理。
    返回结构包含每位用户的行为/标签数据。
    """
    # 统一解析为datetime对象
    start_time_dt = parse_iso_time(start_time)
    end_time_dt = parse_iso_time(end_time)

    user_ids = [m["user_id"] for m in member_list]
    # print("📋 活跃用户 user_ids:", user_ids)
    # print("🧪 extract_chunk_data inputs:", {"group_id": group_id, "start_time": start_time, "end_time": end_time})

    def filter_time_range(item_start, item_end=None):
        start = parse_iso_time(item_start)
        end = parse_iso_time(item_end) if item_end else None
        if not start:
            return False
        if end:
            # 有开始和结束，判断区间是否有交集
            return (start_time_dt <= start <= end_time_dt) or (start_time_dt <= end <= end_time_dt)
        else:
            return start_time_dt <= start <= end_time_dt

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
    note_edit_history = []
    if member_list:
        for m in member_list:
            uid = m["user_id"]
            query = db.collection("note_edit_history").where(filter=FieldFilter("userId", "==", uid)).stream()
            note_edit_history.extend([doc.to_dict() for doc in query])

    filtered_note_edit_history = []
    for e in note_edit_history:
        ts = parse_iso_time(e.get("updatedAt"))
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
        ws = parse_iso_time(b.get("windowStart"))
        we = parse_iso_time(b.get("windowEnd"))
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
        ts = parse_iso_time(n.get("updatedAt", ""))
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
        "speech_counts": speech_counts,
        "current_user": current_user
    }

    # 查询anomaly_analysis_results表，获取current_user的前两次AI分析历史
    try:
        results = db.collection("anomaly_analysis_results") \
            .where("group_id", "==", group_id) \
            .where("current_user.user_id", "==", current_user["user_id"]) \
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
    except Exception as e:
        print("查询anomaly_analysis_results历史失败：", e)
        chunk_data["anomaly_history"] = None

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

def build_anomaly_history_input(chunk_data: dict) -> dict:
    """
    构建用于异常历史分析的输入结构。
    """
    return {
        "current_user": chunk_data.get("current_user"),
        "anomaly_history": chunk_data.get("anomaly_history")
    }