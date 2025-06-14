import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from app.preprocessor_summary import (
    build_cognitive_input,
    build_behavior_input,
    build_attention_input
)
import concurrent.futures

# ✅ 加载 .env
load_dotenv()

# ✅ 设置环境变量供 SDK 使用
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_cognitive(chunk_data: dict) -> dict:
    model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")

    input_data = build_cognitive_input(chunk_data)
    messages = [
        {
            "role": "user",
            "parts": [
                {
                    "text": "你是一位认知评估专家，擅长分析小组成员在协作过程中的思维深度与观点贡献，依据发言和写作内容判断其认知参与等级。\n\n请根据下列小组发言记录与文档协作内容，输出每位成员的 cognitive_level（Passive / Active / Constructive / Interactive），以及整体小组的平均认知参与等级、偏好和总结建议。\n\n以下是小组数据：\n"
                    + json.dumps(input_data, ensure_ascii=False, indent=2)
                    + "\n请按照以下 JSON 格式输出：\n{\n  \"member_levels\": { \"name1\": \"等级\", \"name2\": \"等级\" },\n  \"group_average_level\": \"...\",\n  \"group_cognitive_bias\": \"...\",\n  \"summary\": \"...\"\n}"
                }
            ]
        }
    ]
    print("🚀 开始调用 [Cognitive AI] ...")
    response = model.generate_content(
        contents=messages,
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    print("✅ [Cognitive AI] 返回结果：", response.text)
    return {"raw_response": response.text}


def analyze_behavior(chunk_data: dict) -> dict:
    model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")

    input_data = build_behavior_input(chunk_data)
    messages = [
        {
            "role": "user",
            "parts": [
                {
                    "text": "你是一位行为参与分析助手，负责根据页面浏览、发言和文档编辑行为评估小组成员的参与活跃度。\n\n请根据成员的页面停留时间、互动次数、切换频率、发言次数与总时长、编辑笔记行为摘要，输出每位成员的 behavior_level（高 / 中 / 低 / 无），并在 group_behavior_summary 中详细分析每个成员在发言、页面操作、文档编辑方面的活跃特征和角色偏好。最后输出群体 behavior_metrics 与行为分布特征。\n\n以下是小组数据：\n"
                    + json.dumps(input_data, ensure_ascii=False, indent=2)
                    + "\n请以以下 JSON 格式输出：\n{\n  \"member_levels\": {\n    \"name1\": \"高\",\n    \"name2\": \"中\"\n  },\n  \"behavior_metrics\": {\n    \"average_speech_time\": 83.2,\n    \"edit_count\": 12,\n    \"click_events\": 45\n  },\n  \"group_behavior_summary\": \"...\"\n}"
                }
            ]
        }
    ]
    print("🚀 开始调用 [Behavior AI] ...")
    response = model.generate_content(
        contents=messages,
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    print("✅ [Behavior AI] 返回结果：", response.text)
    return {"raw_response": response.text}


def analyze_attention(chunk_data: dict) -> dict:
    model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")

    input_data = build_attention_input(chunk_data)
    messages = [
        {
            "role": "user",
            "parts": [
                {
                    "text": "你是会议注意力分析助手，负责判断团队成员在本轮讨论中是否保持在相似任务页面与核心内容上，识别注意力一致性与分散趋势。\n\n请输出每人 shared_attention_score（集中 / 中等 / 分散），并为每位成员提供简要的注意力特征分析（如是否聚焦任务页面、是否偏离话题等）；输出群体 group_attention_n_state（同步 / 偏移 / 极分散），并给出注意力偏离的解释与建议。\n\n以下是小组数据：\n"
                    + json.dumps(input_data, ensure_ascii=False, indent=2)
                    + "\n请以以下 JSON 格式输出：\n{\n  \"shared_attention_score\": {\n    \"name1\": \"集中\",\n    \"name2\": \"中等\"\n  },\n  \"group_attention_n_state\": \"...\",\n  \"attention_explanation\": \"...\",\n  \"suggestion\": \"...\"\n}"
                }
            ]
        }
    ]
    print("🚀 开始调用 [Attention AI] ...")
    response = model.generate_content(
        contents=messages,
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    print("✅ [Attention AI] 返回结果：", response.text)
    return {"raw_response": response.text}