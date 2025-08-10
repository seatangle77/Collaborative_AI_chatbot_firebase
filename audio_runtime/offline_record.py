import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import firebase_admin
from firebase_admin import credentials


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


def txt_to_firestore_entries(txt_path, group_key, group_id, session_id, user_map, base_time_str):
    # 初始化 Firebase（如未初始化）
    if not firebase_admin._apps:
        cred_path = Path("firebase-key.json")
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred, {
            'databaseURL': f"https://{cred.project_id}-default-rtdb.asia-southeast1.firebasedatabase.app"
        })

    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配每条语音
    pattern = re.compile(r"\[(\d+:\d+\.\d+),(\d+:\d+\.\d+),(\d+)\]\s+(.*)")
    for match in pattern.finditer(content):
        start_str, end_str, speaker_id, text = match.groups()
        # 时间转换
        def to_time(s):
            m, s = s.split(":")
            return timedelta(minutes=int(m), seconds=float(s))
        base_time = parse_iso_time(base_time_str)
        s_time = base_time + to_time(start_str)
        e_time = base_time + to_time(end_str)
        user_info = user_map.get(speaker_id, {})
        entry = {
            "transcript_id": str(uuid.uuid4()),
            "group_key": group_key,
            "group_id": group_id,
            "session_id": session_id,
            "user_id": user_info.get("user_id",""),
            "speaker": user_info.get("speaker",""),
            "text": text,
            "start": s_time.isoformat(),
            "end": e_time.isoformat(),
            "duration": round((e_time - s_time).total_seconds(), 1)
        }
        # 写入 Firestore
        # firestore.client().collection("speech_transcripts_offline").document(entry["transcript_id"]).set(entry)
        print(f"{entry}")

if __name__ == "__main__":
    ...
    input_file = "./config/group01_config.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        file_analysis_config = json.load(f)
    file_path = file_analysis_config.get('file_path')
    txt_to_firestore_entries(file_path,file_analysis_config['group_key'], file_analysis_config['group_id'], file_analysis_config['session_id'], file_analysis_config['user_map'], file_analysis_config['base_time_str'])
