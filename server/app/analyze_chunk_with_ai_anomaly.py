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
    speech_counts_json = json.dumps(chunk_data.get('speech_counts', {}), ensure_ascii=False, indent=2)
    speech_durations_json = json.dumps(chunk_data.get('speech_durations', {}), ensure_ascii=False, indent=2)
    stage1_duration = time.time() - stage1_start
    print(f"📋 [AI分析] 阶段1-构建输入数据完成，耗时{stage1_duration:.2f}秒")

    # 阶段2: 构建提示词
    stage2_start = time.time()
    prompt_text = f"""
你是一个多维度小组协作分析专家，专门分析**当前用户**在小组讨论中的异常、正常或突出表现，并对比其他组员，并对你自己的分析内容进行自我打分。

【当前小组任务说明】
当前小组正在进行一个开放式探究任务，主题从以下四个议题中选取：
- Labubu 机器人：潮玩爆火背后的「情绪智能」？
- 周末特种兵：年轻人「极限式放松」的真实诉求？
- 宠物心声翻译器：人与宠物关系的「AI进化」？
- 寻找「完美搭子」：轻量社交的算法匹配可能吗？

任务要求成员根据所选议题，主动搜集相关资料（如论坛、社交媒体、用户评论、新闻报道、学术研究等），进行小组讨论，并在协作编辑工具中共同汇总一份包含关键发现、构想建议及证据支持的完整总结文档。小组需要先分析现象背后的心理与社会动因，再提出初步的工具或产品构想，注重真实依据与可行性。

当前用户信息如下（用于分析时请重点关注）：
current_user: {current_user_json}

历史数据（请用于history_comparison分析）：
anomaly_history: {anomaly_history_json}

状态类型（包含异常、正常与积极表现，供参考）：

- 行为缺失：依赖行为、认知、注意力；典型表现为几乎无发言、编辑、浏览
- 认知停滞：依赖认知；典型表现为重复内容、无新观点
- 任务偏离：依赖认知、注意力；典型表现为内容跑题、访问无关页面
- 互动缺失：依赖认知、行为；典型表现为缺少回应、无互动
- 注意力分散：依赖注意力、行为；典型表现为频繁切换、浏览无关内容
- 正常参与：依赖三类数据均衡；典型表现为稳定参与，符合要求
- 行为积极：依赖行为；典型表现为发言编辑多、信息搜集活跃
- 认知引领：依赖认知；典型表现为创新观点、引发思考
- 任务聚焦：依赖认知、注意力；典型表现为高度聚焦任务目标
- 互动促进：依赖认知、行为；典型表现为高频回应、促进协作
- 注意力专注：依赖注意力、行为；典型表现为长时间专注、稳定浏览

【页面相关性判断说明】
- 目标页面：与所选议题相关的新闻、学术文章、社交评论、论坛讨论、调研报告、专业博客，用于资料收集、观点支持和任务推进。
- 无关页面：娱乐、购物、游戏、私聊、与任务完全无关的内容（如追剧、网购、体育八卦等）。

type: 状态类型（包含异常、正常与积极表现），必须从以上类型中选择

认知数据：{cognitive_json}
行为数据：{behavior_json}
注意力数据：{attention_json}
发言统计数据：{speech_counts_json}
发言时长数据：{speech_durations_json}

请结合以上数据，自动选择最合适的状态类型（可能为异常、正常或积极表现），并生成以下信息（这些字段为必填，必须返回）：
    
- type: 状态类型（包含异常、正常与积极表现），必须从上面类型中选择
- status: 当前状态描述，必须根据实际数据动态生成
- evidence: 必须根据数据提取的具体证据
- suggestion: 必须提供针对性的、可执行的建议

此外，为了支持「More」按钮，请额外生成扩展信息，包括：
- detailed_reasoning: 状态出现的详细成因分析（无论是异常还是积极表现）
- history_comparison: 与用户历史状态或上次状态的对比（必须结合anomaly_history数据进行分析）
- group_comparison: 当前用户与小组其他成员的对比情况（如参与度、任务聚焦、活跃度、发言次数和发言时长）
- collaboration_strategies: 可能的协作策略，鼓励与具体成员协作

【重要：内容格式要求】
请严格按照以下JSON格式输出，并在具体内容中使用markdown样式格式，让内容更易读：

{{
  "summary": "一句话总结本轮状态",
  
  "glasses_summary": "你当前[根据数据生成的状态描述]，建议[根据数据生成的行动建议]",
  
  "detail": {{
    "type": "状态类型（包含异常、正常与积极表现）",
    "status": "根据数据生成的状态描述",
    "evidence": "证据1\n- 证据2\n- 证据3",
    "suggestion": "针对性建议"
  }},
  
  "more_info": {{
    "detailed_reasoning": "状态出现的详细成因分析（无论是异常还是积极表现）...\n\n**影响因素：**\n- 因素1\n- 因素2",
    "history_comparison": "| 指标 | 上次 | 本次 | 变化 |\n|------|------|------|------|\n| 参与度 | 85% | 60% | ↓25% |\n| 发言次数 | 12 | 7 | ↓5 |",
    "group_comparison": "**当前用户 vs 其他成员：**\n- **发言活跃度：** 低于平均水平30%\n- **任务聚焦度：** 中等水平\n- **协作参与度：** 需要提升",
    "collaboration_strategies": "**推荐协作对象：**\n- **Alice：** 注意力集中，可帮助聚焦\n- **Bob：** 经验丰富，可提供指导\n\n**具体策略：**\n1. 主动向Alice请教当前话题\n2. 与Bob结对完成复杂任务"
  }},
  
  "user_data_summary": {{
    "speaking_count": 7,
    "speaking_duration": 45.2,
    "reply_count": 1,
    "edit_count": 3,
    "page_view_count": 8,
    "page_switch_frequency": 4,
    "group_avg_comparison": {{
      "speaking_diff": 0,
      "speaking_duration_diff": 5.2,
      "reply_diff": -3,
      "edit_diff": -1,
      "page_focus_diff": -2
    }},
    "group_speech_distribution": {{
      "current_user_speeches": 5,
      "current_user_duration": 45.2,
      "other_members": {{
        "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2": {{
          "count": 5,
          "duration": 52.4
        }},
        "HGa3L2y3eSf7KXYQs793vLWnQRu2": {{
          "count": 3,
          "duration": 28.6
        }}
      }},
      "group_total": 13,
      "group_total_duration": 126.2
    }}
  }},
  
  "score": {{
    "state_score": 70,
    "content_similarity_score": 40,
    "score_reason": "请结合下方评分维度与说明进行自我评价，并输出评分原因",
    "should_notify": true
  }}

}}

【眼镜版本要求】
- glasses_summary：必须是一句话，以"你"开头，简洁明了
- 适合在眼镜小屏幕上显示
- 包含状态类型和简单建议
- 必须根据当前用户的实际数据动态生成，不要使用固定示例
- 示例格式："你当前[具体状态]，建议[具体行动]"
- 根据speech_count、edit_count、page_switch_frequency等数据生成个性化提醒

【内容样式指南】
- 使用 **粗体** 突出重要信息
- 使用 *斜体* 强调关键概念
- 使用列表（- 或 1.）组织信息
- 使用表格对比数据
- 使用分隔线（---）区分不同部分
- 使用换行和缩进提高可读性

评分维度与说明（你对自己上述分析内容的自我打分）：

💡 状态评分：根据当前状态评估，异常<40，正常40–75，积极表现>75，用于判断是否需要提示或鼓励
💡 内容相似度评分：根据与历史 anomaly_history 的内容相似度（若无历史，则默认0），相似度高（>80%）得80分，低（<20%）得20分。

⚠️ 注意：仅输出这两个分数，并根据以下阈值决定是否提示：
- 当状态评分 < 25 或 > 75 时，建议提示
- 当内容相似度评分 < 50 时，也建议提示

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