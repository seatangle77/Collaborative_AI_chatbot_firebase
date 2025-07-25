import json
import os
import re
import time
import uuid
from datetime import timezone, datetime

import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel

from server.app.anomaly_preprocessor import (
    build_anomaly_history_input
)
from server.app.database import db
from server.app.logger.logger_loader import logger


class Member(BaseModel):
    id: str
    name: str

class CurrentUser(BaseModel):
    user_id: str
    name: str
    device_token: str

# 优先加载 .env.local（如果有），再加载 .env
load_dotenv('.env.local')
load_dotenv()

# ✅ 设置环境变量供 SDK 使用
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ai_analyze_all_anomalies(chunk_data: dict) -> dict:
    total_start_time = time.time()
    logger.info(f"🚀 [AI分析] 开始调用Gemini AI进行异常分析...")

    model = genai.GenerativeModel("gemini-1.5-flash")

    # 阶段1: 构建输入数据
    stage1_start = time.time()
    anomaly_history_input = None
    anomaly_history_json = None
    try:
        anomaly_history_input = build_anomaly_history_input(chunk_data)
        anomaly_history_json = json.dumps(anomaly_history_input, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("未能获取anomaly_history_input：", e)
        anomaly_history_json = "null"

    current_user_json = json.dumps(chunk_data.get('current_user', {}), ensure_ascii=False, indent=2)
    speech_counts_json = json.dumps(chunk_data.get('speech_counts', {}), ensure_ascii=False, indent=2)
    speech_durations_json = json.dumps(chunk_data.get('speech_durations', {}), ensure_ascii=False, indent=2)
    stage1_duration = time.time() - stage1_start
    logger.info(f"📋 [AI分析] 阶段1-构建输入数据完成，耗时{stage1_duration:.2f}秒")

    # 阶段2: 构建提示词
    stage2_start = time.time()
    prompt_text = f"""
你是一个多维度小组协作分析专家。系统已经为一个小组中的三位成员提供了完整的行为评分结果，包括发言、编辑、浏览等级和总得分（不需要你重新判断）。你的任务是：

🔹 基于 total_level 判断该成员的参与状态；
🔹 输出温和鼓励的眼镜提示语（glasses_summary）；
🔹 给出该成员的状态类型、行为结构描述、建议与证据；
🔹 提供更详细的多角度分析，包括历史对比、小组对比与协作建议；
🔹 补充该小组在各个总参与等级（low/normal/high/dominant）中的成员人数统计（group_distribution 字段）。

🎯 所有提示必须语气正向、亲和，不得批评；
🎯 glasses_summary 应适配眼镜小屏幕，使用一句简洁中文，可含颜文字；
🎯 输出字段结构必须完全符合下方格式；

【参与等级与提示规则】
- total_level = "No Participation" → 明确提示激活；
- total_level = "Low Participation" → 鼓励表达与操作；
- total_level = "Normal Participation" → 无需提示；
- total_level = "High Participation" → 温和提示协作平衡；
- total_level = "Dominant" → 委婉提示留出他人空间。

【输出结构】
请为每位成员输出以下 JSON 结构（共 3 组）：

{{
  "成员名": {{
    "summary": "一句话总结当前状态",
    "glasses_summary": "你当前[状态]，建议[温和提示]",
    "detail": {{
      "type": "参与状态类型，如 Low Participation",
      "status": "简洁描述该成员的当前行为结构",
      "evidence": "- 发言等级：{speech_level}\\n- 编辑等级：{note_edit_level}\\n- 浏览等级：{browser_level}",
      "suggestion": "行为层面的改善建议，如主动表达、协同参与等"
    }},
    "more_info": {{
      "detailed_reason": "你为何判断该成员为该状态的详细解释",
      "history_comparison": "与该成员过往轮次的比较分析",
      "group_comparison": "与当前组内其他成员的对比说明",
      "collaboration_suggestion": "结合协同角度的具体建议，例如带动他人/让出表达空间等"
    }},
    "group_distribution": {{
      "no": X,
      "low": X,
      "normal": X,
      "high": X,
      "dominant": X
    }}
  }},
  ...
}}

📌 注意事项：
- 所有字段必须填写完整，避免输出模板占位符；
- 若成员无需提醒，`glasses_summary` 仍需输出空字符串，但 `should_notify` 字段应为 false；
- group_distribution 统计的是该小组中不同 total_level 的人数（你将收到或推理）；

你现在将收到 3 位成员的数据，请输出上述结构。
"""
    stage2_duration = time.time() - stage2_start
    logger.info(f"📝 [AI分析] 阶段2-构建提示词完成，耗时{stage2_duration:.2f}秒")

    # 阶段3: 调用AI模型
    stage3_start = time.time()
    logger.info("🚀 [AI分析] 开始调用 [Anomaly AI 综合分析] ...")
    response = model.generate_content(
        contents=[{"role": "user", "parts": [{"text": prompt_text}]}],
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    stage3_duration = time.time() - stage3_start
    logger.info(f"✅ [AI分析] 阶段3-AI调用完成，耗时{stage3_duration:.2f}秒")
    logger.info(f"✅ [AI分析] [Anomaly AI] 返回结果：", response.text)

    total_duration = time.time() - total_start_time
    logger.info(f"✅ [AI分析] Gemini AI异常分析完成，总耗时{total_duration:.2f}秒")

    return {"raw_response": response.text}

async def ai_analyze_anomaly_status(group_id: str, start_time: str, end_time: str, chunk_data: dict):
    total_start_time = time.time()
    logger.info(f"🚀 [异常分析] 开始分析group_id={group_id}...")

    # 阶段2: AI分析
    stage2_start = time.time()
    result = ai_analyze_all_anomalies(chunk_data)
    stage2_duration = time.time() - stage2_start
    logger.info(f"🤖 [异常分析] 阶段2-AI分析完成，耗时{stage2_duration:.2f}秒")

    # 阶段3: 结果解析
    stage3_start = time.time()
    # 解析AI返回的JSON结果

    summary = None
    glasses_summary = None
    detail = None
    user_data_summary = None
    more_info = None
    score = None
    should_push = False
    try:
        if isinstance(result.get("raw_response"), str):
            raw = result["raw_response"]
            # 用正则提取出 {...} 部分
            match = re.search(r"{[\s\S]*}", raw)
            if match:
                json_str = match.group(0)
                parsed_result = json.loads(json_str)
                summary = parsed_result.get("summary")
                glasses_summary = parsed_result.get("glasses_summary", "你当前状态需要关注")
                detail = parsed_result.get("detail")
                user_data_summary = parsed_result.get("user_data_summary")
                more_info = parsed_result.get("more_info")
                score = parsed_result.get("score")

                # 根据score的状态评分和内容相似度评分判断是否推送
                if score and isinstance(score, dict):
                    state_score = score.get("state_score")
                    content_similarity_score = score.get("content_similarity_score")
                    should_push = False
                    if state_score is not None and content_similarity_score is not None:
                        should_push = (state_score < 25 or state_score > 75) and (content_similarity_score < 50)
                        logger.info(
                            f"📊 [异常分析] 状态评分：{state_score}，内容相似度评分：{content_similarity_score}，推送阈值：状态评分<25或>75，内容相似度评分<50，是否推送：{should_push}")
                    else:
                        should_push = True  # 如果没有评分信息，默认推送
                        logger.info(f"⚠️ [异常分析] 未找到完整评分信息，默认推送")
                else:
                    should_push = False  # 如果没有score信息，默认不推送
                    logger.info(f"⚠️ [异常分析] 未找到评分信息，默认不推送")
            else:
                glasses_summary = "你当前状态需要关注"
                should_push = True
        else:
            glasses_summary = "你当前状态需要关注"
            should_push = True
    except Exception as e:
        logger.info("解析AI响应失败：", e)
        glasses_summary = "你当前状态需要关注"
        should_push = True
    stage3_duration = time.time() - stage3_start
    logger.info(f"📝 [异常分析] 阶段3-结果解析完成，耗时{stage3_duration:.2f}秒")

    # 阶段4: 文件存储
    stage4_start = time.time()
    # 保存分析结果为文件

    os.makedirs("analysis_outputs", exist_ok=True)
    file_name = f"analysis_outputs/anomaly_{uuid.uuid4()}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    stage4_duration = time.time() - stage4_start
    logger.info(f"💾 [异常分析] 阶段4-文件存储完成，耗时{stage4_duration:.2f}秒")

    # 阶段5: 数据库存储
    stage5_start = time.time()
    # 新建 anomaly_analysis_files 表并插入内容
    file_id = str(uuid.uuid4())
    db.collection("anomaly_raw_json_input").document(file_id).set({
        "id": file_id,
        "group_id": group_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": result  # 完整分析内容
    })

    # 新建anomaly_analysis_results表并插入数据
    analysis_id = str(uuid.uuid4())
    db.collection("anomaly_analysis_results").document(analysis_id).set({
        "id": analysis_id,
        "group_id": group_id,
        "start_time": start_time,
        "end_time": end_time,
        "raw_response": result.get("raw_response"),
        "summary": summary,
        "glasses_summary": glasses_summary,
        "detail": detail,
        "user_data_summary": user_data_summary,
        "more_info": more_info,
        "score": score,
        "should_push": should_push,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    stage5_duration = time.time() - stage5_start
    logger.info(f"🗄️ [异常分析] 阶段5-数据库存储完成，耗时{stage5_duration:.2f}秒")


    total_duration = time.time() - total_start_time
    logger.info(f"✅ [异常分析] group_id={group_id}分析完成，总耗时{total_duration:.2f}秒")

    # 返回给前端更多信息
    return {
        "raw_response": result.get("raw_response"),
        "summary": summary,
        "glasses_summary": glasses_summary,
        "detail": detail,
        "user_data_summary": user_data_summary,
        "more_info": more_info,
        "score": score,
        "should_push": should_push,
        "group_id": group_id,
        "start_time": start_time,
        "end_time": end_time,
        "analysis_id": analysis_id,
        "anomaly_analysis_results_id": analysis_id  # 添加兼容字段
    }

def calculate_total_score_and_level(speech_score_dict, edit_score_dict, browser_score_dict, chunk_data):
    user_ids = [user['user_id'] for user in chunk_data.get('users', [])]
    total_score = {}
    total_level = {}
    for uid in user_ids:
        speech = speech_score_dict.get(uid, 0)
        edit = edit_score_dict.get(uid, 0)
        browser = browser_score_dict.get(uid, 0)
        score = speech * 0.7 + edit * 0.15 + browser * 0.15
        total_score[uid] = round(score, 3)
        # 等级判定
        if score == 0:
            level = "No Participation"
        elif 0 < score <= 0.3:
            level = "Low Participation"
        elif 0.3 < score < 0.7:
            level = "Normal Participation"
        elif 0.7 <= score < 0.9:
            level = "High Participation"
        else:  # 0.9 <= score <= 1
            level = "Dominant"
        total_level[uid] = level
    return total_score, total_level

def local_analyze_anomaly_status(chunk_data):
    """
    统计：
    1. speech_transcripts：按user统计总说话时长、占time_range百分比。
    2. pageBehaviorLogs：按user统计浏览网页数、总action次数、鼠标操作总时长及占time_range百分比。
    返回：{user_id: {...}}
    """
    def parse_time(t):
        if not t:
            return None
        try:
            return datetime.fromisoformat(t.replace('Z', '+00:00'))
        except Exception:
            return None

    time_start = parse_time(chunk_data['time_range']['start'])
    time_end = parse_time(chunk_data['time_range']['end'])
    total_seconds = (time_end - time_start).total_seconds() if time_start and time_end else 1

    # speech_transcripts统计
    speech_map = {}
    for item in chunk_data.get('raw_tables', {}).get('speech_transcripts', []):
        uid = item.get('user_id')
        dur = item.get('duration', 0)
        if uid:
            speech_map.setdefault(uid, 0)
            speech_map[uid] += dur
    total_speech = sum(speech_map.values())

    # pageBehaviorLogs统计
    page_logs = chunk_data.get('raw_tables', {}).get('pageBehaviorLogs', {})
    page_stats = {}
    for uname, pdata in page_logs.items():
        user = pdata.get('user', {})
        uid = user.get('user_id')
        tabHistory = pdata.get('tabHistory', [])
        page_count = len(tabHistory)
        action_count = 0
        mousemove_duration = 0.0
        for tab in tabHistory:
            for log in tab.get('tabBehaviorLogs', []):
                action_count += log.get('action_count', 0)
                if log.get('type') in ['mousemove', 'scroll']:
                    st = parse_time(log.get('startTime'))
                    et = parse_time(log.get('endTime'))
                    if st and et:
                        mousemove_duration += (et - st).total_seconds()
        mousemove_percent = round(mousemove_duration / total_seconds * 100, 2) if total_seconds else 0
        page_stats[uid] = {
            'page_count': page_count,
            'mouse_action_count': action_count,
            'mouse_duration': f"{round(mousemove_duration, 2)}s",
            'mouse_percent': f"{mousemove_percent}%"
        }
    # note_edit_history 统计
    note_edit_logs = chunk_data.get('raw_tables', {}).get('note_edit_history', [])
    note_edit_stats = {}
    total_edit_char_count = 0
    for item in note_edit_logs:
        uid = item.get('userId')
        if uid not in note_edit_stats:
            note_edit_stats[uid] = {
                'note_edit_count': 0,
                'note_edit_char_count': 0,
            }
        note_edit_stats[uid]['note_edit_count'] += 1
        for edit in item.get('delta', []):
            if "insert" in edit:
                note_edit_stats[uid]['note_edit_char_count'] += len(edit.get('insert', ""))
                total_edit_char_count += len(edit.get('insert', ""))
            elif "delete" in edit:
                note_edit_stats[uid]['note_edit_char_count'] += edit.get('delete', 0)
                total_edit_char_count += edit.get('delete', 0)


    # 统计发言等级和分数
    speech_level_dict, speech_score_dict = classify_speech_level(speech_map, total_speech, total_seconds, chunk_data)
    # 统计编辑等级和分数
    edit_level_dict, edit_score_dict = classify_note_edit_level(note_edit_stats, total_edit_char_count, chunk_data)
    # 统计浏览器行为等级和分数
    browser_level_dict, browser_score_dict = classify_browser_behavior_level(page_stats, chunk_data)

    # 计算总分和总等级
    total_score_dict, total_level_dict = calculate_total_score_and_level(speech_score_dict, edit_score_dict, browser_score_dict, chunk_data)

    # 合并结果
    result = {}
    for user in chunk_data.get('users', []):
        uid = user['user_id']
        uname = user.get('name', '')
        speech_duration = round(speech_map.get(uid, 0), 2)
        speech_percent = round(speech_duration / total_seconds * 100, 2) if total_seconds else 0
        page_info = page_stats.get(uid, {'page_count':0,'mouse_action_count':0,'mouse_duration':'0s','mouse_percent':'0%'})
        result[uid] = {
            'name': uname,
            'speech_duration': f"{speech_duration}s",
            'speech_percent': f"{speech_percent}%",
            'page_count': page_info.get('page_count', 0),
            'mouse_action_count': page_info.get('mouse_action_count', 0),
            'mouse_duration': page_info.get('mouse_duration', '0s'),
            'mouse_percent': page_info.get('mouse_percent', '0%'),
            'note_edit_count': note_edit_stats.get(uid, {}).get('note_edit_count', 0),
            'note_edit_char_count': note_edit_stats.get(uid, {}).get('note_edit_char_count', 0),
            'speech_level': speech_level_dict.get(uid, "No Speech"),
            'speech_level_score': speech_score_dict.get(uid, 0),
            'note_edit_level': edit_level_dict.get(uid, "No Edit"),
            'note_edit_score': edit_score_dict.get(uid, 0),
            'browser_level': browser_level_dict.get(uid, "No Browsing"),
            'browser_score': browser_score_dict.get(uid, 0),
            'total_score': total_score_dict.get(uid, 0),
            'total_level': total_level_dict.get(uid, "No Participation")
        }
    return result

def classify_speech_level(speech_map, total_speech, total_seconds, chunk_data):
    user_ids = [user['user_id'] for user in chunk_data.get('users', [])]
    speech_durations = [speech_map.get(uid, 0) for uid in user_ids]
    speech_percents = [d / total_speech if total_speech else 0 for d in speech_durations]

    # 分类
    speech_level = {}
    speech_score = {}
    for idx, uid in enumerate(user_ids):
        duration = speech_durations[idx]
        percent = speech_percents[idx]
        if duration == 0:
            speech_level[uid] = "No Speech"
            speech_score[uid] = 0
        elif (total_speech < total_seconds / 3.0):
            # 所有人发言时长不到总时长3分之一
            speech_level[uid] = "Low Speech"
            speech_score[uid] = 0.3
        else:
            if percent < 0.3:
                speech_level[uid] = "Low Speech"
                speech_score[uid] = 0.3
            elif percent >= 0.7:
                speech_level[uid] = "High Speech"
                speech_score[uid] = 1
            else:
                speech_level[uid] = "Normal Speech"
                speech_score[uid] = 0.7
    return speech_level, speech_score

def classify_note_edit_level(note_edit_stats, total_edit_char_count, chunk_data):
    user_ids = [user['user_id'] for user in chunk_data.get('users', [])]
    edit_level = {}
    edit_score = {}

    for uid in user_ids:
        count = note_edit_stats.get(uid, {}).get('note_edit_count', 0)
        chars = note_edit_stats.get(uid, {}).get('note_edit_char_count', 0)
        percent = chars / total_edit_char_count if total_edit_char_count else 0
        if count == 0:
            edit_level[uid] = "No Edit"
            edit_score[uid] = 0
        elif percent < 0.3:
            edit_level[uid] = "Few Edits"
            edit_score[uid] = 0.3
        elif 0.3 <= percent < 0.7:
            edit_level[uid] = "Normal Edit"
            edit_score[uid] = 0.7
        elif percent >= 0.7:
            edit_level[uid] = "Frequent Edit"
            edit_score[uid] = 1
        else:
            edit_level[uid] = "No Edit"
            edit_score[uid] = 0
    return edit_level, edit_score

def classify_browser_behavior_level(page_stats, chunk_data):
    user_ids = [user['user_id'] for user in chunk_data.get('users', [])]
    browser_level = {}
    browser_score = {}
    for uid in user_ids:
        stats = page_stats.get(uid, {})
        action_count = stats.get('mouse_action_count', 0)
        try:
            percent = float(str(stats.get('mouse_percent', '0')).replace('%', ''))
        except Exception:
            percent = 0
        if action_count == 0:
            browser_level[uid] = "No Browsing"
            browser_score[uid] = 0
        elif percent < 30:
            browser_level[uid] = "Few Browsing"
            browser_score[uid] = 0.3
        elif 30 <= percent < 70:
            browser_level[uid] = "Normal Browsing"
            browser_score[uid] = 0.7
        elif percent >= 70:
            browser_level[uid] = "Frequent Browsing"
            browser_score[uid] = 1
        else:
            browser_level[uid] = "No Browsing"
            browser_score[uid] = 0
    return browser_level, browser_score

if __name__ == '__main__':
    ...

    input_file = "../debug_anomaly_outputs/chunk_data_18b4c9cf636e45e8829738b96f4f53bb_merge1.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    print(json.dumps(local_analyze_anomaly_status(logs), ensure_ascii=False, indent=2))