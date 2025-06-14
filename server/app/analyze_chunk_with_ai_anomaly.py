import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from app.preprocessor_anomaly import (
    build_cognitive_anomaly_input,
    build_behavior_anomaly_input,
    build_attention_anomaly_input
)
import concurrent.futures

# ✅ 加载 .env
load_dotenv()

# ✅ 设置环境变量供 SDK 使用
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_all_anomalies(chunk_data: dict) -> dict:
    model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")

    cognitive_input = build_cognitive_anomaly_input(chunk_data)
    behavior_input = build_behavior_anomaly_input(chunk_data)
    attention_input = build_attention_anomaly_input(chunk_data)

    prompt_text = f"""
你是一个多维度小组分析专家，负责识别协作过程中的三类异常：认知偏差、行为异常、注意力偏移。

异常参考类型如下（供你参考并进行判断）：

[
  {{
    "type": "行为缺失",
    "status": "本轮行为参与度偏低",
    "evidence": "未发言，Notion编辑记录为空，无浏览任务页面",
    "suggestion": "尝试分享你查到的内容，或提出一个问题引发讨论。"
  }},
  {{
    "type": "行为偏离",
    "status": "行为关注偏离任务",
    "evidence": "页面停留过久、频繁跳页或聚焦无关内容",
    "suggestion": "回到与你当前任务相关的页面，关注小组当前主题。"
  }},
  {{
    "type": "内容重复",
    "status": "认知参与度较低",
    "evidence": "文本重复率高，相似句式占比较高",
    "suggestion": "尝试换一个角度发言，或对比他人观点后补充思考。"
  }},
  {{
    "type": "无回应",
    "status": "缺乏回应行为",
    "evidence": "无引用、无提问、无接续发言行为",
    "suggestion": "主动对他人观点做出回应，促进更深入的对话。"
  }},
  {{
    "type": "任务偏移",
    "status": "你的注意力与小组方向不一致",
    "evidence": "组内页面热度图 + 当前浏览记录不一致",
    "suggestion": "查看组员正在关注的内容，寻找共同切入点。"
  }},
  {{
    "type": "分布分散",
    "status": "团队关注过于分散",
    "evidence": "无明显共页访问，页面热度均匀",
    "suggestion": "是否需要选出焦点话题或共同搜索路径？"
  }}
]

认知数据：{json.dumps(cognitive_input, ensure_ascii=False, indent=2)}

行为数据：{json.dumps(behavior_input, ensure_ascii=False, indent=2)}

注意力数据：{json.dumps(attention_input, ensure_ascii=False, indent=2)}

请从上述数据中判断最可能的异常类型，并输出简洁摘要和详细建议，格式如下：

{{
  "summary": "你当前浏览内容与小组方向略有偏移，可聚焦当前讨论主题。",
  "detail": {{
    "type": "任务偏移",
    "status": "你的注意力与小组方向不一致",
    "evidence": "组内页面热度图 + 当前浏览记录不一致",
    "suggestion": "查看组员正在关注的内容，寻找共同切入点。"
  }}
}}
"""

    print("🚀 开始调用 [Anomaly AI 综合分析] ...")
    response = model.generate_content(
        contents=[{"role": "user", "parts": [{"text": prompt_text}]}],
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    print("✅ [Anomaly AI] 返回结果：", response.text)

    return {"raw_response": response.text}