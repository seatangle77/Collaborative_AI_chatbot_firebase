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
                         prompt_type: str = "cognitive_guidance", model: str = "default"):
    """
    使用 google-genai 官方 Client 接口调用 Gemini 模型（标准推荐用法）
    """
    try:
        if prompt_type != "cognitive_guidance":
            raise ValueError(f"❌ Unsupported prompt_type: {prompt_type}")

        system_prompt = "你是一个小组讨论助理，请根据团队讨论内容判断是否需要引导并提供建议，最多不超过 {max_words} 字。"
        system_prompt = system_prompt.replace("{max_words}", str(100))

        # ✅ 构造用户内容
        user_prompt = f"请根据以下讨论内容，判断是否需要引导团队进一步讨论，并提供知识支持：\n\n{main_prompt}"

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
