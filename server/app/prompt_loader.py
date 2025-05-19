import json
from app.database import supabase_client

def get_prompt_from_database(bot_id: str, prompt_type: str, agent_id: str = None) -> dict:
    """
    从 ai_bots 表中，根据 bot_id 和 prompt_type 获取对应的 system prompt 和 max_words。

    参数:
    - bot_id: str, 机器人 ID
    - prompt_type: str, 提示类型，可为:
      - 'real_time_summary'
      - 'cognitive_guidance'

    返回格式:
    {
        "system_prompt": "string",
        "max_words": int,
        "prompt_type": str
    }
    """
    if prompt_type == "term_explanation":
        if not agent_id:
            raise ValueError("❌ term_explanation 类型需要提供 agent_id")
        
        response = supabase_client.table("personal_agents").select("personal_prompt").eq("id", agent_id).execute()
        if not response.data:
            raise ValueError(f"❌ 没有找到 agent_id 为 {agent_id} 的记录")
        
        record = response.data[0]
        personal_prompt_str = record.get("personal_prompt")

        return {
            "max_words": 80,
            "system_prompt": personal_prompt_str or "",
            "prompt_type": prompt_type
        }

    response = supabase_client.table("ai_bots").select("discussion_prompt", "knowledge_prompt", "config").eq("id", bot_id).execute()

    if not response.data:
        raise ValueError(f"❌ 没有找到 bot_id 为 {bot_id} 的记录")

    record = response.data[0]
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
