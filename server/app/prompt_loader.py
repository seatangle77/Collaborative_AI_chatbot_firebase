import json
from app.database import db as firestore_client

def get_prompt_from_database(bot_id: str, prompt_type: str, agent_id: str = None) -> dict:
    if prompt_type == "term_explanation":
        if not agent_id:
            raise ValueError("❌ term_explanation 类型需要提供 agent_id")

        doc = firestore_client.collection("personal_agents").document(agent_id).get()
        if not doc.exists:
            raise ValueError(f"❌ 没有找到 agent_id 为 {agent_id} 的记录")

        personal_prompt_str = doc.to_dict().get("personal_prompt", "")
        return {
            "max_words": 80,
            "system_prompt": personal_prompt_str,
            "prompt_type": prompt_type
        }

    doc = firestore_client.collection("ai_bots").document(bot_id).get()
    if not doc.exists:
        raise ValueError(f"❌ 没有找到 bot_id 为 {bot_id} 的记录")

    record = doc.to_dict()
    raw_config = record.get("config")
    config = json.loads(raw_config if raw_config else "{}")

    if prompt_type == "real_time_summary":
        return {
            "max_words": config.get("real_time_summary", {}).get("max_words", 100),
            "system_prompt": config.get("real_time_summary", {}).get("system_prompt") or record.get("knowledge_prompt"),
            "prompt_type": prompt_type
        }
    elif prompt_type == "cognitive_guidance":
        return {
            "max_words": config.get("cognitive_guidance", {}).get("max_words", 100),
            "system_prompt": config.get("cognitive_guidance", {}).get("system_prompt") or record.get("discussion_prompt"),
            "prompt_type": prompt_type
        }
    else:
        raise ValueError(f"❌ 不支持的 prompt_type: {prompt_type}")
