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
import time

# 优先加载 .env.local（如果有），再加载 .env
load_dotenv('.env.local')
load_dotenv()

# ✅ 设置环境变量供 SDK 使用
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_all_anomalies(chunk_data: dict) -> dict:
    total_start_time = time.time()
    print(f"🚀 [AI分析] 开始调用Gemini AI进行异常分析...")
    
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 阶段1: 构建输入数据
    stage1_start = time.time()
    cognitive_input = build_cognitive_anomaly_input(chunk_data)
    behavior_input = build_behavior_anomaly_input(chunk_data)
    attention_input = build_attention_anomaly_input(chunk_data)
    anomaly_history_input = None
    anomaly_history_json = None
    try:
        from app.preprocessor_anomaly import build_anomaly_history_input
        anomaly_history_input = build_anomaly_history_input(chunk_data)
        anomaly_history_json = json.dumps(anomaly_history_input, ensure_ascii=False, indent=2)
    except Exception as e:
        print("未能获取anomaly_history_input：", e)
        anomaly_history_json = "null"

    current_user_json = json.dumps(chunk_data.get('current_user', {}), ensure_ascii=False, indent=2)
    cognitive_json = json.dumps(cognitive_input, ensure_ascii=False, indent=2)
    behavior_json = json.dumps(behavior_input, ensure_ascii=False, indent=2)
    attention_json = json.dumps(attention_input, ensure_ascii=False, indent=2)
    stage1_duration = time.time() - stage1_start
    print(f"📋 [AI分析] 阶段1-构建输入数据完成，耗时{stage1_duration:.2f}秒")

    # 阶段2: 构建提示词
    stage2_start = time.time()
    prompt_text = f"""
你是一个多维度小组协作分析专家，专门分析**当前用户**在小组讨论中的异常状态，并对比其他组员。

当前用户信息如下（用于分析时请重点关注）：
current_user: {current_user_json}

历史数据（请用于history_comparison分析）：
anomaly_history: {anomaly_history_json}

异常类型（供参考）：
- 行为缺失：长时间未发言、无编辑或无浏览
- 认知停滞：内容重复或无新观点
- 任务偏离：讨论方向与小组整体不一致
- 互动缺失：缺乏引用、提问或对他人回应
- 注意力分散：页面访问分散，跳跃式发言

认知数据：{cognitive_json}
行为数据：{behavior_json}
注意力数据：{attention_json}

请结合以上数据，自动选择最合适的异常类型，并生成以下信息（这些字段为必填，必须返回）：
- type: 异常类型，必须从上面五类中选择
- status: 当前状态描述，必须根据实际数据动态生成
- evidence: 必须根据数据提取的具体证据
- suggestion: 必须提供针对性的、可执行的建议

此外，为了支持「More」按钮，请额外生成扩展信息，包括：
- detailed_reasoning: 异常出现的详细成因分析
- history_comparison: 与用户历史状态或上次异常的对比（必须结合anomaly_history数据进行分析）
- group_comparison: 当前用户与小组其他成员的对比情况（如参与度、任务聚焦、活跃度）
- collaboration_strategies: 可能的协作策略，鼓励与具体成员协作

【新增要求】
请在JSON输出中增加一个user_data_summary字段，结构如下，内容需基于数据自动生成：
user_data_summary: {{
  "speaking_count": 7,
  "reply_count": 1,
  "edit_count": 3,
  "page_view_count": 8,
  "page_switch_frequency": 4,
  "group_avg_comparison": {{
    "speaking_diff": 0,
    "reply_diff": -3,
    "edit_diff": -1,
    "page_focus_diff": -2
  }}
}}

【重要：内容格式要求】
请严格按照以下JSON格式输出，并在具体内容中使用markdown样式格式，让内容更易读：

{{
  "summary": "一句话总结本轮异常",
  
  "glasses_summary": "你当前[根据数据生成的异常描述]，建议[根据数据生成的行动建议]",
  
  "detail": {{
    "type": "异常类型",
    "status": "根据数据生成的状态描述",
    "evidence": "证据1\n- 证据2\n- 证据3",
    "suggestion": "针对性建议"
  }},
  
  "more_info": {{
    "detailed_reasoning": "异常出现的根本原因是...\n\n**影响因素：**\n- 因素1\n- 因素2",
    "history_comparison": "| 指标 | 上次 | 本次 | 变化 |\n|------|------|------|------|\n| 参与度 | 85% | 60% | ↓25% |\n| 发言次数 | 12 | 7 | ↓5 |",
    "group_comparison": "**当前用户 vs 其他成员：**\n- **发言活跃度：** 低于平均水平30%\n- **任务聚焦度：** 中等水平\n- **协作参与度：** 需要提升",
    "collaboration_strategies": "**推荐协作对象：**\n- **Alice：** 注意力集中，可帮助聚焦\n- **Bob：** 经验丰富，可提供指导\n\n**具体策略：**\n1. 主动向Alice请教当前话题\n2. 与Bob结对完成复杂任务"
  }},
  
  "user_data_summary": {{
    "speaking_count": 7,
    "reply_count": 1,
    "edit_count": 3,
    "page_view_count": 8,
    "page_switch_frequency": 4,
    "group_avg_comparison": {{
      "speaking_diff": 0,
      "reply_diff": -3,
      "edit_diff": -1,
      "page_focus_diff": -2
    }}
  }},
  
  "score": {{
    "置信度": 90,
    "建议明确性": 85,
    "输出重复惩罚": 10,
    "提示间隔惩罚": 20,
    "总评分": 76.75,
    "是否提示": true
  }}
}}

【眼镜版本要求】
- glasses_summary：必须是一句话，以"你"开头，简洁明了
- 适合在眼镜小屏幕上显示
- 包含异常类型和简单建议
- 必须根据当前用户的实际数据动态生成，不要使用固定示例
- 示例格式："你当前[具体异常]，建议[具体行动]"
- 根据speech_count、edit_count、page_switch_frequency等数据生成个性化提醒

【内容样式指南】
- 使用 **粗体** 突出重要信息
- 使用 *斜体* 强调关键概念
- 使用列表（- 或 1.）组织信息
- 使用表格对比数据
- 使用分隔线（---）区分不同部分
- 使用换行和缩进提高可读性

评分维度与说明：
- 置信度：是否基于充分数据准确判断异常（权重0.65）
- 建议明确性：是否提供清晰、可执行建议（权重0.35）
- 输出重复惩罚：连续同类异常时，是否减少提示（扣分-0.25）
- 提示间隔惩罚：与上次提示是否过短（<4分钟则扣分-0.25）

总评分计算公式：
总评分 = (置信度 * 0.65) + (建议明确性 * 0.35) - (输出重复惩罚 * 0.25) - (提示间隔惩罚 * 0.25)

请严格按照上述 JSON 格式一次性完整输出，所有必填字段必须生成，便于后续解析。
"""
    stage2_duration = time.time() - stage2_start
    print(f"📝 [AI分析] 阶段2-构建提示词完成，耗时{stage2_duration:.2f}秒")

    # 阶段3: 调用AI模型
    stage3_start = time.time()
    print("🚀 [AI分析] 开始调用 [Anomaly AI 综合分析] ...")
    response = model.generate_content(
        contents=[{"role": "user", "parts": [{"text": prompt_text}]}],
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    stage3_duration = time.time() - stage3_start
    print(f"✅ [AI分析] 阶段3-AI调用完成，耗时{stage3_duration:.2f}秒")
    print(f"✅ [AI分析] [Anomaly AI] 返回结果：", response.text)

    total_duration = time.time() - total_start_time
    print(f"✅ [AI分析] Gemini AI异常分析完成，总耗时{total_duration:.2f}秒")

    return {"raw_response": response.text}