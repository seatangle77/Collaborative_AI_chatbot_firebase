import json
import os
import time
import traceback
import uuid
from datetime import timezone, datetime
from typing import Union

import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel

from server.app.anomaly_preprocessor import (
    get_group_members_simple, parse_iso_time, extract_chunk_data_anomaly
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

def ai_analyze_all_anomalies(chunk_data_with_local_analyze: dict) -> tuple[str, dict]:
    total_start_time = time.time()
    logger.info(f"🚀 [AI分析] 开始调用Gemini AI进行异常分析...")

    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt_text = f"""
【用户行为数据】='''{chunk_data_with_local_analyze}'''

【任务描述】='''
你是一个多维度小组协作分析专家。系统已经为一个小组中的三位成员提供了完整的行为评分结果，包括发言、编辑、浏览等级和总得分（无需你重新判断）。你的任务是：

🔹 基于 total_level 判断该成员的参与状态；
🔹 输出温和鼓励的眼镜提示语（glasses_summary）；
🔹 给出该成员的状态类型、行为结构描述、建议与证据；
🔹 提供更详细的多角度分析，包括历史对比、小组对比与协作建议；
🔹 输出该小组的整体参与结构 group_distribution，包括五类参与等级的数量统计与结构洞察（如类型、风险、建议）；
🔹 明确指出是否需要进行提示（字段 should_notify）。

🎯 所有提示必须语气正向、亲和，避免批评；
🎯 glasses_summary 必须适配智能眼镜的小屏幕，内容简洁、友好，**必须使用颜文字（如 ^_^、>_<、(๑•̀ㅂ•́)و✧），严禁使用 emoji 图标（如 😊、👍 等）**；
🎯 输出内容必须严格符合下方格式。
'''

【参与等级与提示规则】='''
- total_level = "No Participation" → 明确提示激活；
- total_level = "Low Participation" → 鼓励表达与操作；
- total_level = "Normal Participation" → 无需提示；
- total_level = "High Participation" → 温和提示协作平衡；
- total_level = "Dominant" → 委婉提示留出他人空间。
'''

【输出结构】='''
请为每位成员输出以下 JSON 结构（共 3 组）：

{{
  "用户ID": {{
    "user_name": "用户名",
    "summary": "一句话总结当前状态",
    "glasses_summary": "建议[温和提示]+颜文字表情,8个字以内",
    "should_notify": true 或 false,
    "detail": {{
      "type": "参与状态类型，如 Low Participation",
      "status": "简洁描述该成员的当前行为结构",
      "evidence": "- 发言等级：High Speech（时长：76.04s，占比：63.37%）\\n- 编辑等级：Normal Edit（次数：2，字符数：637）\\n- 浏览等级：Normal Browsing（页面数：2，浏览时长：61.13s，占比：50.94%）",
      "suggestion": "行为层面的改善建议，如主动表达、协同参与等"
    }},
    "more_info": {{
      "detailed_reason": "你为何判断该成员为该状态的详细解释，引用具体数据进行推理，如发言时长、编辑字数、mouse行为等",
      "history_comparison": "与该成员过往轮次的比较分析，如“本轮发言时长比上一轮增加 20s”",
      "group_comparison": "与当前组内其他成员的对比说明，如“发言最多，比平均值高出 40%”",
      "collaboration_suggestion": "结合协同角度的具体建议，例如主动让出空间、邀请他人表达等",
      "extra_data": "可补充 mouse_action_count、mouse_duration、mouse_percent、total_score 等信息"
    }},
    "group_distribution": {{
      "no": X,
      "low": X,
      "normal": X,
      "high": X,
      "dominant": X,
      "group_type": "结构类型，如 失衡型 / 均衡型 / 高参与组 / 低参与组",
      "group_risk": "结构潜在风险，如 主导者明显 + 多人低参与",
      "action_hint": "群体层级建议，如 激励低参与成员 + 鼓励主导者留出空间"
    }}
  }},
  ...
}}
'''

【注意事项】='''
- 所有字段必须填写完整，不得留空或使用模板占位符；
- evidence 必须包含行为等级 + 原始数据（如发言时长、编辑次数、页面数、浏览时长等）；
- more_info 字段需结合行为数据进行深入分析与比较，不得使用笼统语言；
- group_distribution 结构中必须包含 group_type、group_risk、action_hint 三项内容；
- 若成员无需提示，glasses_summary 仍应输出空字符串，should_notify 应为 false；
'''

你现在收到 3 位成员的数据，请输出上述结构。
"""

    logger.info("🚀 [AI分析] 开始调用 [Anomaly AI 综合分析] ...")
    response = model.generate_content(
        contents=[{"role": "user", "parts": [{"text": prompt_text}]}],
        generation_config=genai.types.GenerationConfig(temperature=0.7)
    )
    logger.info(f"✅ [AI分析] [Anomaly AI] 返回结果：", response.text)

    total_duration = time.time() - total_start_time
    logger.info(f"✅ [AI分析] Gemini AI异常分析完成，总耗时{total_duration:.2f}秒")

    return prompt_text, {"raw_response": response.text}

def ai_analyze_anomaly_status(group_id: str, chunk_data: dict):
    total_start_time = time.time()
    logger.info(f"🚀 [异常分析] 开始分析group_id={group_id}...")

    start_time = chunk_data['time_range']['start']
    end_time = chunk_data['time_range']['end']

    # 阶段2: AI分析
    prompt, ai_analyze_result = ai_analyze_all_anomalies(chunk_data)

    # 阶段3: 结果解析
    try:
        if isinstance(ai_analyze_result.get("raw_response"), str):
            markdown_json = ai_analyze_result["raw_response"]
            # 去除Markdown标记
            json_str = markdown_json.strip('```json').strip('\n').strip('```').strip()
            ai_analyze_result_json = json.loads(json_str)

            try:
                # 阶段4: 文件存储
                stage4_start = time.time()
                os.makedirs("analysis_outputs", exist_ok=True)
                file_name = f"analysis_outputs/ai_analysis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(ai_analyze_result_json, f, ensure_ascii=False, indent=2)
                stage4_duration = time.time() - stage4_start
                logger.info(f"💾 [异常分析] 阶段4-文件存储完成，耗时{stage4_duration:.2f}秒")

                # 阶段5: 数据库存储
                stage5_start = time.time()
                # 新建 anomaly_analysis_files 表并插入内容
                file_id = str(uuid.uuid4())
                db.collection("anomaly_raw_json_in_out").document(file_id).set({
                    "id": file_id,
                    "group_id": group_id,
                    "created_at": end_time,
                    "input": prompt,
                    "output": ai_analyze_result_json
                })

                # 新建anomaly_analysis_group_results表并插入数据
                analysis_id = str(uuid.uuid4())
                db.collection("anomaly_analysis_group_results").document(analysis_id).set({
                    "id": analysis_id,
                    "group_id": group_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "raw_response": ai_analyze_result_json,
                    "created_at": end_time
                })
                stage5_duration = time.time() - stage5_start
                logger.info(f"🗄️ [异常分析] 阶段5-数据库存储完成，耗时{stage5_duration:.2f}秒")

                total_duration = time.time() - total_start_time
                logger.info(f"✅ [异常分析] group_id={group_id}分析完成，总耗时{total_duration:.2f}秒")
            except Exception as e:
                logger.error('AI解析结果保存异常： %s' % traceback.format_exc())

                # 异常情况保存
                # 阶段4: 文件存储
                logger.warning(f"💾 [异常分析] 结果异常，保存现场")
                os.makedirs("analysis_outputs", exist_ok=True)
                file_name = f"analysis_outputs/ai_analysis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(ai_analyze_result, f, ensure_ascii=False, indent=2)

                # 阶段5: 数据库存储
                stage5_start = time.time()
                file_id = str(uuid.uuid4())
                db.collection("anomaly_raw_json_in_out").document(file_id).set({
                    "id": file_id,
                    "group_id": group_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "input": prompt,
                    "output": ai_analyze_result
                })
                stage5_duration = time.time() - stage5_start
                logger.info(f"🗄️ [异常分析] 结果异常，保存现场。数据库存储完成，耗时{stage5_duration:.2f}秒")

                total_duration = time.time() - total_start_time
                logger.info(f"✅ [异常分析] 结果异常，保存现场。group_id={group_id}分析完成，总耗时{total_duration:.2f}秒")

            # 返回给前端更多信息
            return ai_analyze_result_json
    except Exception as e:
        logger.error('解析AI响应失败： %s' % traceback.format_exc())

    return {}

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
            # 所有人发言市场超过总时长3分之一，按每个人的发言相对比例计算
            if percent < 0.15:
                speech_level[uid] = "Low Speech"
                speech_score[uid] = 0.3
            elif percent >= 0.6:
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

def local_analyze_anomaly_status(chunk_data) -> tuple[dict, dict]:
    """
    统计：
    1. speech_transcripts：按user统计总说话时长、占time_range百分比。
    2. pageBehaviorLogs：按user统计浏览网页数、总action次数、鼠标操作总时长及占time_range百分比。
    返回：{user_id: {...}}
    """
    time_start_dt = parse_iso_time(chunk_data['time_range']['start'])
    time_end_dt = parse_iso_time(chunk_data['time_range']['end'])
    total_seconds = (time_end_dt - time_start_dt).total_seconds() if time_start_dt and time_end_dt else 1


    # speech_transcripts统计
    # 语言输出可能跨越统计周期，只计算落在当前语言周期的时长
    speech_map = {}
    for item in chunk_data.get('raw_tables', {}).get('speech_transcripts', []):
        uid = item.get('user_id')
        start = parse_iso_time(item.get('start'))
        end = parse_iso_time(item.get('end'))
        if start < time_start_dt:
            start = time_start_dt
        if end > time_end_dt:
            end = time_end_dt
        if uid:
            speech_map.setdefault(uid, 0)
            speech_map[uid] += (end - start).total_seconds()
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
                    st = parse_iso_time(log.get('startTime'))
                    et = parse_iso_time(log.get('endTime'))
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
    local_analyze_result = {}
    for user in chunk_data.get('users', []):
        uid = user['user_id']
        uname = user.get('name', '')
        speech_duration = round(speech_map.get(uid, 0), 2)
        speech_percent = round(speech_duration / total_seconds * 100, 2) if total_seconds else 0
        page_info = page_stats.get(uid, {'page_count':0,'mouse_action_count':0,'mouse_duration':'0s','mouse_percent':'0%'})
        local_analyze_result[uid] = {
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

    # 合并本地分析结果到 chunk_data
    chunk_data['local_analysis_result'] = local_analyze_result

    return chunk_data, local_analyze_result

def local_analyze(group_id:str, start_time:Union[datetime,str], end_time:Union[datetime,str], is_save_debug_info:bool = True) -> tuple[dict, dict]:
    # 阶段1: 获取成员信息
    start_time_1 = time.time()
    members = get_group_members_simple(group_id)
    logger.info(f"📊 [异常分析] 阶段1-获取成员信息完成，耗时{(time.time() - start_time_1):.2f}秒")

    # 阶段2: 数据预处理
    start_time_2 = time.time()
    if isinstance(start_time, datetime):
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        start_time_str = start_time
    if isinstance(end_time, datetime):
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        end_time_str = end_time
    raw_data, increment = extract_chunk_data_anomaly(
        group_id=group_id,
        round_index=1,
        start_time=start_time_str,
        end_time=end_time_str,
        member_list=members
    )
    logger.info(f"📊 [异常分析] 阶段2-数据预处理完成，耗时{time.time() - start_time_2:.2f}秒")
    if increment <= 0:
        logger.warning("[异常分析] 用户活动数据增量为0，不做分析")
        return {}, {}

    # 阶段3：本地数据分析
    chunk_data_with_local_analyze, local_analyze_result = local_analyze_anomaly_status(raw_data)

    # 阶段4：保存调试文件
    if is_save_debug_info:
        os.makedirs("analysis_outputs", exist_ok=True)
        debug_file_path = f"analysis_outputs/local_analysis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        with open(debug_file_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data_with_local_analyze, f, ensure_ascii=False, indent=2)

        # 阶段5: 数据库存储
        stage5_start = time.time()
        file_id = str(uuid.uuid4())
        db.collection("anomaly_local_analyze").document(file_id).set({
            "id": file_id,
            "group_id": group_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "output": chunk_data_with_local_analyze
        })
        stage5_duration = time.time() - stage5_start
        logger.info(f"🗄️ [异常分析] 本地分析。数据库存储完成，耗时{stage5_duration:.2f}秒")

    return chunk_data_with_local_analyze, local_analyze_result




if __name__ == '__main__':
    ...
    # # 分析文件记录
    # input_file = "../debug_anomaly_outputs/chunk_data_18b4c9cf636e45e8829738b96f4f53bb_merge1.json"
    # with open(input_file, 'r', encoding='utf-8') as f:
    #     logs = json.load(f)
    # print(json.dumps(local_analyze_anomaly_status(logs), ensure_ascii=False, indent=2))

    # 查询数据，分析结果
    group_id = "cc8f1d29-7a49-4975-95dc-7ac94aefc04b"
    start_time_str = "2025-07-10T07:02:27"
    end_time_str = "2025-07-10T07:04:27"
    members = get_group_members_simple(group_id)
    raw_data, increment = extract_chunk_data_anomaly(
        group_id=group_id,
        round_index=1,
        start_time=start_time_str,
        end_time=end_time_str,
        member_list=members
    )
    chunk_data_with_local_result, local_analyze_result = local_analyze_anomaly_status(raw_data)
    # prompt, ai_analyze_result = ai_analyze_all_anomalies(chunk_data_with_local_result)
    # if isinstance(ai_analyze_result.get("raw_response"), str):
    #     markdown_json = ai_analyze_result["raw_response"]
    #     # 去除Markdown标记
    #     json_str = markdown_json.strip('```json').strip('\n').strip('```').strip()
    #     print(json.dumps(json.loads(json_str), ensure_ascii=False, indent=2))

    ai_analyze_anomaly_status(group_id, chunk_data_with_local_result)
