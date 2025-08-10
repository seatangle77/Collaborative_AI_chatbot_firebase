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
        print(f"✅ 已写入: {entry}")

if __name__ == "__main__":
    ...
    base_data = {
        "group_key": "group01",
        "group_id": "99ea0701-f656-4960-83c4-0a09d39e856f",
        "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
        "user_map": {
            "0": {"speaker": "Terry", "user_id": "AMgf8LZrTSdg03xY7HYfLsuhQjH2"},
            "1": {"speaker": "Ally", "user_id": "EMf4aBZbXzO4RL8xNwAf3BPmkFh1"},
            "2": {"speaker": "Shirao", "user_id": "zN8ugpSZseMHty0la3MM9YKNGtj2"}
        },
        "base_time_str": "2025-07-30 14:52:18"
    }
    file_path = "D:/PythonProject/Collaborative_AI_chatbot_firebase/audio_runtime/offline_recognition/通用语音识别_海康_G01_无辅助_搞抽象.m4a.txt"
    txt_to_firestore_entries(file_path,base_data['group_key'], base_data['group_id'], base_data['session_id'], base_data['user_map'], base_data['base_time_str'])
