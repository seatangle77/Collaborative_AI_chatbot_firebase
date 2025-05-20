import os
import json
import requests
from dotenv import load_dotenv
from app.database import db
import google.generativeai as genai
import traceback


# ✅ 加载 .env
load_dotenv()

# ✅ 设置环境变量供 SDK 使用
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai


def generate_ai_response(bot_id: str, main_prompt: str, history_prompt: str = None,
                         prompt_type: str = "real_time_summary", model: str = "default", agent_id: str = None):
    """
    使用 google-genai 官方 Client 接口调用 Gemini 模型（标准推荐用法）
    """
    try:
        # ✅ 从新版表获取 prompt 数据
        if prompt_type in ["real_time_summary", "cognitive_guidance", "summary_to_knowledge"]:
            if not bot_id:
                raise ValueError(f"{prompt_type} 类型必须提供 bot_id")
            table = "ai_prompt_versions"
            id_field = "ai_bot_id"
            id_value = bot_id
        elif prompt_type in ["term_explanation", "knowledge_followup"]:
            if not agent_id:
                raise ValueError(f"{prompt_type} 类型必须提供 agent_id")
            table = "agent_prompt_versions"
            id_field = "agent_id"
            id_value = agent_id
        else:
            raise ValueError(f"❌ Unsupported prompt_type: {prompt_type}")

        docs = (
            db.collection(table)
            .where(id_field, "==", id_value)
            .where("prompt_type", "==", prompt_type)
            .where("is_active", "==", True)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )

        docs = list(docs)
        if not docs:
            raise ValueError(f"❌ No active prompt found for {prompt_type}")

        system_prompt = docs[0].to_dict()["rendered_prompt"]
        max_words = 150 if prompt_type == "real_time_summary" else 100
        system_prompt = system_prompt.replace("{max_words}", str(max_words))

        # ✅ 构造用户内容
        if prompt_type == "real_time_summary":
            user_prompt = f"请在 {max_words} 词以内总结以下内容：\n\n{main_prompt}"
        elif prompt_type == "cognitive_guidance":
            user_prompt = f"请根据以下讨论内容，判断是否需要引导团队进一步讨论，并提供知识支持：\n\n{main_prompt}"
        elif prompt_type == "term_explanation":
            user_prompt = f"请在 {max_words} 词以内解释这个术语：\n\n{main_prompt}"
        else:
            return f"❌ 不支持的 prompt_type: {prompt_type}"

        # ✅ 组合内容（system + user + optional history）
        contents = [system_prompt, user_prompt]
        if history_prompt:
            contents.append(history_prompt)

        # ✅ 映射模型名
        model = "gemini-2.5-pro-exp-03-25"
        model_name = model

        print("📤 使用模型:", model_name)
        print("📤 组合 prompt 内容如下：\n", "\n\n".join(contents))

        # ✅ 调用 Gemini API（非流式版本）
        response = client.models.generate_content(
            model=model_name,
            contents=[{"role": "user", "parts": [{"text": "\n\n".join(contents)}]}],
        )

        print("📥 原始响应对象:", response)
        print("📥 响应文本内容:", response.candidates[0].content.parts[0].text.strip())

        return response.candidates[0].content.parts[0].text.strip()

    except Exception as e:
        print(f"❌ Gemini API 调用失败: {e}")
        traceback.print_exc()
        return f"AI 生成失败，请稍后再试。错误详情: {str(e)}"
