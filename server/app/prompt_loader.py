import json
from app.database import db as firestore_client

def get_prompt_from_database(bot_id: str, prompt_type: str) -> dict:
    doc = firestore_client.collection("ai_bots").document(bot_id).get()
    if not doc.exists:
        raise ValueError(f"❌ 没有找到 bot_id 为 {bot_id} 的记录")

    record = doc.to_dict()
    raw_config = record.get("config")
    config = json.loads(raw_config if raw_config else "{}")

    raise ValueError(f"❌ 不支持的 prompt_type: {prompt_type}")
