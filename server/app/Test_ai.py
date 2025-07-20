import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from server.app.anomaly_preprocessor import (
  build_cognitive_anomaly_input,
  build_behavior_anomaly_input,
  build_attention_anomaly_input, build_anomaly_history_input
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

# 测试代码 - 直接运行此文件时执行
if __name__ == "__main__":
    print("🚀 开始测试 analyze_all_anomalies 方法...")
    print("=" * 60)
    
    # 示例测试数据
    test_chunk_data = {
  "time_range": {
    "start": "2025-07-08T13:03:05",
    "end": "2025-07-08T13:05:05"
  },
  "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
  "users": [
    {
      "user_id": "HGa3L2y3eSf7KXYQs793vLWnQRu2",
      "name": "TestUser2",
      "speech_count": 0,
      "speech_duration": 0
    },
    {
      "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
      "name": "TestUser1",
      "speech_count": 0,
      "speech_duration": 0
    },
    {
      "user_id": "9WW5I5naK6U20OIQulZEhLOvzWR2",
      "name": "TestUser3",
      "speech_count": 0,
      "speech_duration": 0
    }
  ],
  "raw_tables": {
    "speech_transcripts": [],
    "note_edit_history": [
      {
        "affectedText": "自我意识崛起，注重个体价值：\nZ世代普遍对自我价值的实现有较高追求，不再像前几代人那样过度关注外部评价和传统权威，而是更注重内心的感受和自我认同。\n追求个性化和自由，拒绝被标签化：\nZ世代普遍追求与众不同，喜欢彰显个性，对各种标签和刻板印象持抵触态度。他们更愿意根据自己的喜好和价值观来塑造自我形象，并以此来表达自我。\n对新事物接受度高，乐于尝试新鲜事物：\nZ世代是在互联网时代成长起来的一代，对新科技、新文化、新观念接受度高，乐于尝试新鲜事物，并积极参与到各种新潮流中。\n社交需求旺盛，热衷社群互动：\nZ世代普遍热衷于社交媒体，热衷于在线互动，追求社群归属感。他们通过社交平台建立人际关系，分享生活，表达观点，寻求共鸣。\n务实理性，对未来充满不确定性：u\nZ世代在追求个性和自由的同时，也表现出一定的务实理性。他们对未来充满不确定性，更注重实际的成长和发展，对物质和精神生活都有着自己的规划。\n\n222222222222222222222222222\n2222222\n22222222222222\n222222222222222222222\n2222222222222222222222222\nssssssssss",
        "hasList": False,
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "charCount": 508,
        "delta": [
          {
            "delete": 508
          }
        ],
        "summary": "删除文字",
        "hasHeader": False,
        "updatedAt": "2025-07-08T13:03:06.179Z",
        "isDelete": True
      },
      {
        "affectedText": "自我意识崛起，注重个体价值：\nZ世代普遍对自我价值的实现有较高追求，不再像前几代人那样过度关注外部评价和传统权威，而是更注重内心的感受和自我认同。\n追求个性化和自由，拒绝被标签化：\nZ世代普遍追求与众不同，喜欢彰显个性，对各种标签和刻板印象持抵触态度。他们更愿意根据自己的喜好和价值观来塑造自我形象，并以此来表达自我。\n对新事物接受度高，乐于尝试新鲜事物：\nZ世代是在互联网时代成长起来的一代，对新科技、新文化、新观念接受度高，乐于尝试新鲜事物，并积极参与到各种新潮流中。\n社交需求旺盛，热衷社群互动：\nZ世代普遍热衷于社交媒体，热衷于在线互动，追求社群归属感。他们通过社交平台建立人际关系，分享生活，表达观点，寻求共鸣。\n务实理性，对未来充满不确定性：u\nZ世代在追求个性和自由的同时，也表现出一定的务实理性。他们对未来充满不确定性，更注重实际的成长和发展，对物质和精神生活都有着自己的规划。\n\n222222222222222222222222222\n2222222\n22222222222222\n222222222222222222222\n2222222222222222222222222\nssssssssss",
        "hasList": False,
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "charCount": 508,
        "delta": [
          {
            "delete": 508
          }
        ],
        "summary": "删除文字",
        "hasHeader": False,
        "updatedAt": "2025-07-08T13:03:17.179Z",
        "isDelete": True
      }
    ],
    "pageBehaviorLogs": [
      {
        "windowEnd": "2025-07-08T13:03:20.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 94,
                "x": 644
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:05.182Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 14,
                "x": 453
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:06.949Z",
              "tabId": 2046891577
            },
            {
              "position": {
                "y": 132,
                "x": 489
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:07.463Z",
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:07.714Z",
              "maxDepth": 0.0015455950540958269,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:08.230Z",
              "maxDepth": 0.6120556414219475,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:08.730Z",
              "maxDepth": 0.6599690880989181,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:09.445Z",
              "maxDepth": 0.999227202472952,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:09.944Z",
              "maxDepth": 0.999227202472952,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:10.579Z",
              "maxDepth": 0.999227202472952,
              "tabId": 2046891577
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:11.080Z",
              "maxDepth": 0.999227202472952,
              "tabId": 2046891577
            },
            {
              "position": {
                "y": 142,
                "x": 494
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:11.713Z",
              "tabId": 2046891577
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:14.443Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:14.443Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "新标签页",
              "timestamp": "2025-07-08T13:03:14.443Z",
              "tabId": 2046891581,
              "url": "chrome://newtab/"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "新标签页",
            "timestamp": "2025-07-08T13:03:12.592Z",
            "tabId": 2046891581,
            "url": "chrome://newtab/"
          }
        },
        "windowStart": "2025-07-08T13:03:10.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:03:30.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:24.441Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:24.441Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "AI 手 - Google Search",
              "timestamp": "2025-07-08T13:03:24.441Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+%E6%89%8B&oq=AI+%E6%89%8B&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQABiABDIHCAIQABiABDIHCAMQABiABDIHCAQQABiABDIHCAUQABiABDIHCAYQABiABDIHCAcQABiABDIHCAgQABiABDIHCAkQLhiABNIBCTYyOTZqMWoxNagCCLACAfEFZKHLjbZdGbE&sourceid=chrome&ie=UTF-8"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "新标签页",
            "timestamp": "2025-07-08T13:03:12.592Z",
            "tabId": 2046891581,
            "url": "chrome://newtab/"
          }
        },
        "windowStart": "2025-07-08T13:03:20.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:03:40.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 267,
                "x": 1065
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:32.896Z",
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:33.397Z",
              "maxDepth": 0.0003091190108191654,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:33.930Z",
              "maxDepth": 0.10108191653786708,
              "tabId": 2046891581
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:34.443Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:34.443Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:03:34.443Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "新标签页",
            "timestamp": "2025-07-08T13:03:12.592Z",
            "tabId": 2046891581,
            "url": "chrome://newtab/"
          }
        },
        "windowStart": "2025-07-08T13:03:30.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:03:50.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:35.181Z",
              "maxDepth": 0.13106646058732613,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:35.696Z",
              "maxDepth": 0.14683153013910355,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:36.197Z",
              "maxDepth": 0.16630602782071097,
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 423,
                "x": 409
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:36.430Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 448,
                "x": 415
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:38.932Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 339,
                "x": 547
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:39.767Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 13,
                "x": 837
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:42.230Z",
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:42.912Z",
              "maxDepth": 0.00013885031935573453,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:44.247Z",
              "maxDepth": 0.006803665648430992,
              "tabId": 2046891585
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:44.444Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:44.444Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:03:44.444Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": True,
              "title": "Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:03:44.444Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "Introducing Gemini, your new personal AI assistant",
            "timestamp": "2025-07-08T13:03:41.385Z",
            "tabId": 2046891585,
            "url": "https://gemini.google/assistant/?hl=en"
          }
        },
        "windowStart": "2025-07-08T13:03:40.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:00.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:44.881Z",
              "maxDepth": 0.007497917245209664,
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 299,
                "x": 791
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:45.297Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 11,
                "x": 945
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:45.831Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 6,
                "x": 933
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:47.275Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 197,
                "x": 877
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:48.109Z",
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:51.796Z",
              "maxDepth": 0.008156791661946302,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:52.297Z",
              "maxDepth": 0.02197802197802198,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:54.030Z",
              "maxDepth": 0.03149427891695933,
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 341,
                "x": 896
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:54.433Z",
              "tabId": 2046891585
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:54.438Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:54.438Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:03:54.438Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": True,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:03:54.438Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "Introducing Gemini, your new personal AI assistant",
            "timestamp": "2025-07-08T13:03:41.385Z",
            "tabId": 2046891585,
            "url": "https://gemini.google/assistant/?hl=en"
          }
        },
        "windowStart": "2025-07-08T13:03:50.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:10.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 2,
                "x": 959
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:55.718Z",
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:56.329Z",
              "maxDepth": 0.03409992069785884,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:57.184Z",
              "maxDepth": 0.06276198028775348,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:58.064Z",
              "maxDepth": 0.09810807748952079,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:03:58.813Z",
              "maxDepth": 0.11476152713266115,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:00.078Z",
              "maxDepth": 0.1478418488727767,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:01.180Z",
              "maxDepth": 0.1905517163249122,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:02.064Z",
              "maxDepth": 0.2200488997555012,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:02.786Z",
              "maxDepth": 0.24449877750611246,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:03.504Z",
              "maxDepth": 0.26693796744390674,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:04.170Z",
              "maxDepth": 0.2939706681151548,
              "tabId": 2046891585
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:04.441Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:04.441Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:04.441Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": True,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:04.441Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "Introducing Gemini, your new personal AI assistant",
            "timestamp": "2025-07-08T13:03:41.385Z",
            "tabId": 2046891585,
            "url": "https://gemini.google/assistant/?hl=en"
          }
        },
        "windowStart": "2025-07-08T13:04:00.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:20.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:05.272Z",
              "maxDepth": 0.3174689021092482,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:06.629Z",
              "maxDepth": 0.34674209092813746,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:07.312Z",
              "maxDepth": 0.37496107131734663,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:08.577Z",
              "maxDepth": 0.39542717158313767,
              "tabId": 2046891585
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:09.963Z",
              "maxDepth": 0.43656454043194376,
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 305,
                "x": 853
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:10.764Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 244,
                "x": 685
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:11.346Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 22,
                "x": 660
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:12.367Z",
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:12.780Z",
              "maxDepth": 0.16723338485316847,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:13.281Z",
              "maxDepth": 0.26553323029366305,
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 363,
                "x": 609
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:13.889Z",
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:14.238Z",
              "maxDepth": 0.3397217928902628,
              "tabId": 2046891581
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:14.442Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:14.442Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:14.442Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:14.442Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "AI assistant - Google Search",
            "timestamp": "2025-07-08T13:04:12.189Z",
            "tabId": 2046891581,
            "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
          }
        },
        "windowStart": "2025-07-08T13:04:10.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:30.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:14.747Z",
              "maxDepth": 0.5777434312210201,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:15.481Z",
              "maxDepth": 0.7508500772797527,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:04:16.097Z",
              "maxDepth": 0.9211746522411128,
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 435,
                "x": 600
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:16.474Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 171,
                "x": 520
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:16.978Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 160,
                "x": 698
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:18.780Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 159,
                "x": 705
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:19.348Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 26,
                "x": 812
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:19.865Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 11,
                "x": 909
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:20.522Z",
              "tabId": 2046891581
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:24.444Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:24.444Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:24.444Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:24.444Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            },
            {
              "active": False,
              "title": "",
              "timestamp": "2025-07-08T13:04:24.444Z",
              "tabId": 2046891588,
              "url": ""
            }
          ],
          "activeTab": {
            "active": True,
            "title": "AI assistant - Google Search",
            "timestamp": "2025-07-08T13:04:12.189Z",
            "tabId": 2046891581,
            "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
          }
        },
        "windowStart": "2025-07-08T13:04:20.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:40.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 611,
                "x": 1082
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:26.352Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 340,
                "x": 844
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:27.091Z",
              "tabId": 2046891581
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:34.445Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:34.445Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:34.445Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:34.445Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            },
            {
              "active": True,
              "title": "reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/",
              "timestamp": "2025-07-08T13:04:34.445Z",
              "tabId": 2046891588,
              "url": "https://www.reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/",
            "timestamp": "2025-07-08T13:04:28.030Z",
            "tabId": 2046891588,
            "url": "https://www.reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/"
          }
        },
        "windowStart": "2025-07-08T13:04:30.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:04:50.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 520,
                "x": 1070
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:42.246Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 497,
                "x": 804
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:42.895Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 566,
                "x": 595
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:43.992Z",
              "tabId": 2046891588
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:44.444Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:44.444Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:44.444Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:44.444Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            },
            {
              "active": True,
              "title": "reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/",
              "timestamp": "2025-07-08T13:04:44.444Z",
              "tabId": 2046891588,
              "url": "https://www.reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/",
            "timestamp": "2025-07-08T13:04:28.030Z",
            "tabId": 2046891588,
            "url": "https://www.reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/"
          }
        },
        "windowStart": "2025-07-08T13:04:40.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:05:00.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 1,
                "x": 749
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:45.205Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 3,
                "x": 776
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:46.521Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 312,
                "x": 667
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:47.196Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 548,
                "x": 473
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:47.699Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 554,
                "x": 472
              },
              "type": "click",
              "count": 1,
              "timestamp": "2025-07-08T13:04:47.934Z",
              "tabId": 2046891588
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:54.439Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:04:54.439Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:04:54.439Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:04:54.439Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            },
            {
              "active": True,
              "title": "Reddit - 互联网的核心",
              "timestamp": "2025-07-08T13:04:54.439Z",
              "tabId": 2046891588,
              "url": "https://www.reddit.com/login/"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/",
            "timestamp": "2025-07-08T13:04:28.030Z",
            "tabId": 2046891588,
            "url": "https://www.reddit.com/r/ArtificialInteligence/comments/1d3p8lu/whats_the_best_ai_personal_assistant/"
          }
        },
        "windowStart": "2025-07-08T13:04:50.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:05:10.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 79,
                "x": 627
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:55.826Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 244,
                "x": 638
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:56.819Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 269,
                "x": 620
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:57.332Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 317,
                "x": 614
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:04:58.049Z",
              "tabId": 2046891588
            },
            {
              "position": {
                "y": 6,
                "x": 901
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:05:00.732Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 30,
                "x": 742
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:05:01.347Z",
              "tabId": 2046891585
            },
            {
              "position": {
                "y": 12,
                "x": 670
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:05:01.986Z",
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:05:02.331Z",
              "maxDepth": 0.9211746522411128,
              "tabId": 2046891581
            },
            {
              "type": "scroll",
              "timestamp": "2025-07-08T13:05:02.881Z",
              "maxDepth": 0.9740340030911901,
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 369,
                "x": 621
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:05:03.346Z",
              "tabId": 2046891581
            },
            {
              "position": {
                "y": 648,
                "x": 496
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:05:04.347Z",
              "tabId": 2046891581
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:05:04.446Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:05:04.446Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": True,
              "title": "AI assistant - Google Search",
              "timestamp": "2025-07-08T13:05:04.446Z",
              "tabId": 2046891581,
              "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
            },
            {
              "active": False,
              "title": "隆重推出 Gemini，您的全新个人 AI 助手 --- Introducing Gemini, your new personal AI assistant",
              "timestamp": "2025-07-08T13:05:04.446Z",
              "tabId": 2046891585,
              "url": "https://gemini.google/assistant/?hl=en"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "AI assistant - Google Search",
            "timestamp": "2025-07-08T13:05:01.846Z",
            "tabId": 2046891581,
            "url": "https://www.google.com/search?q=AI+assistant&sca_esv=06aa7bafa5db9320&sxsrf=AE3TifNmXtK1x0NnYePubDCHIVLoaZIJyw%3A1751979800439&ei=GBdtaLbFGvjh2roPquGM0Qo"
          }
        },
        "windowStart": "2025-07-08T13:05:00.000Z"
      },
      {
        "windowEnd": "2025-07-08T13:03:10.000Z",
        "userId": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
        "behaviorData": {
          "tabBehaviorLogs": [
            {
              "position": {
                "y": 92,
                "x": 659
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:02:58.243Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 221,
                "x": 531
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:02:58.746Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 221,
                "x": 531
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:02:59.637Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 221,
                "x": 531
              },
              "type": "click",
              "count": 1,
              "timestamp": "2025-07-08T13:03:00.931Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 220,
                "x": 532
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:01.146Z",
              "tabId": 2046891520
            },
            {
              "position": {
                "y": 148,
                "x": 671
              },
              "type": "mousemove",
              "timestamp": "2025-07-08T13:03:01.647Z",
              "tabId": 2046891520
            }
          ],
          "user": {
            "session_id": "5ab15191-a1e6-40ca-b3b7-1cb880c558e8",
            "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
            "group_id": "fcdf6669-745a-44e0-88b9-5c361e78d31e",
            "userName": "TestUser1"
          },
          "tabHistory": [
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:04.437Z",
              "tabId": 2046891520,
              "url": "http://localhost:3000/#/public-display/Group%20G"
            },
            {
              "active": False,
              "title": "Collaborative Platform",
              "timestamp": "2025-07-08T13:03:04.437Z",
              "tabId": 2046891577,
              "url": "http://localhost:3000/#/personal-dashboard/TestUser1"
            },
            {
              "active": False,
              "title": "扩展程序",
              "timestamp": "2025-07-08T13:03:04.437Z",
              "tabId": 2046891580,
              "url": "chrome://extensions/"
            },
            {
              "active": True,
              "title": "新标签页",
              "timestamp": "2025-07-08T13:03:04.437Z",
              "tabId": 2046891581,
              "url": "chrome://newtab/"
            }
          ],
          "activeTab": {
            "active": True,
            "title": "新标签页",
            "timestamp": "2025-07-08T13:03:03.138Z",
            "tabId": 2046891581,
            "url": ""
          }
        },
        "windowStart": "2025-07-08T13:03:00.000Z"
      }
    ],
    "unique_note_contents": []
  },
  "speech_counts": {},
  "speech_durations": {},
  "current_user": {
    "user_id": "GJp4Y7cLhDh9RCM6c7ua4mgSbWz2",
    "name": "TestUser1",
    "device_token": "160a3797c92315ac0e3"
  },
  "anomaly_history": None
}
    
    try:
        # 调用分析方法
        result = analyze_all_anomalies(test_chunk_data)
        
        print("\n" + "=" * 60)
        print("✅ 方法调用成功！")
        print("=" * 60)
        print("📋 返回的 raw_response:")
        print("=" * 60)
        
        # 打印原始响应
        raw_response = result.get("raw_response", "无响应")
        print(raw_response)
        print("=" * 60)
        
        # 尝试解析JSON
        try:
            import json
            parsed_response = json.loads(raw_response)
            print("✅ JSON解析成功！")
            print("📋 解析后的JSON结构:")
            print(json.dumps(parsed_response, ensure_ascii=False, indent=2))
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            print("原始响应可能不是有效的JSON格式")
            
    except Exception as e:
        print(f"❌ 方法调用失败: {e}")
        import traceback
        traceback.print_exc()