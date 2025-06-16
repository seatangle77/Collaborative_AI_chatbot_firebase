from fastapi import Body
from typing import Dict, Any, List
# 模拟缓存：用于暂存 interval summary 结果
interval_summary_cache: Dict[str, List[Dict[str, Any]]] = {}

# Firebase Admin SDK 导入与初始化
from firebase_admin import messaging, credentials, initialize_app
import firebase_admin
import os
if not len(firebase_admin._apps):
    cred = credentials.Certificate("./server/firebase-key.json")
    initialize_app(cred)

from fastapi import APIRouter, Query, HTTPException
import json
from pydantic import BaseModel
#
from app.preprocessor_summary import extract_chunk_data
from app.preprocessor_anomaly import extract_chunk_data_anomaly
from app.analyze_chunk_with_ai import analyze_cognitive, analyze_behavior, analyze_attention
from app.analyze_chunk_with_ai_anomaly import analyze_all_anomalies

router = APIRouter()

class Member(BaseModel):
    id: str
    name: str

class IntervalSummaryRequest(BaseModel):
    group_id: str
    round_index: int
    start_time: str
    end_time: str
    members: List[Member]


# 替换为 POST 方法，参数结构同 IntervalSummaryRequest，通过请求体接收
@router.post("/analysis/anomalies")
async def get_anomaly_status(req: IntervalSummaryRequest):
    members = [{"user_id": m.id, "name": m.name} for m in req.members]

    raw_data = extract_chunk_data_anomaly(
        group_id=req.group_id,
        round_index=req.round_index,
        start_time=req.start_time,
        end_time=req.end_time,
        member_list=members
    )
    result = analyze_all_anomalies(raw_data)
    # 保存分析结果为文件
    import uuid
    from datetime import datetime
    os.makedirs("analysis_outputs", exist_ok=True)
    file_name = f"analysis_outputs/anomaly_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 发送推送通知到客户端
    from firebase_admin import firestore
    db = firestore.client()

    # 写死 user_id
    target_user_id = "0AlcY0xmqSTWXxAm2f5cT0tNEbJ3"
    user_doc = db.collection("users_info").document(target_user_id).get()
    if user_doc.exists:
        device_token = user_doc.to_dict().get("device_token")
        if device_token:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="📡 异常分析完成",
                    body="新的异常检测结果已生成，点击查看分析详情。"
                ),
                token=device_token
            )
            try:
                response = messaging.send(message)
                print("✅ 推送成功:", response)
            except Exception as e:
                print("❌ 推送失败:", e)
        else:
            print("⚠️ 用户未设置 device_token")
    else:
        print("❌ 用户不存在:", target_user_id)

    return result


@router.post("/analysis/interval_summary")
async def interval_summary(req: IntervalSummaryRequest):
    """
    每5分钟自动分析一次，将段落分析结果暂存（模拟缓存）。
    """
    import uuid
    from datetime import datetime
    import os

    members = [{"user_id": m.id, "name": m.name} for m in req.members]

    # 通过 extract_chunk_data 获取 chunk 数据
    chunk_data = extract_chunk_data(
        group_id=req.group_id,
        round_index=req.round_index,
        start_time=req.start_time,
        end_time=req.end_time,
        member_list=members
    )
    #print("🧪 chunk_data result:", chunk_data)

    cog_result = analyze_cognitive(chunk_data)
    beh_result = analyze_behavior(chunk_data)
    attn_result = analyze_attention(chunk_data)

    os.makedirs("analysis_outputs", exist_ok=True)
    result = {
        "cognitive": cog_result,
        "behavior": beh_result,
        "attention": attn_result
    }
    file_name = f"analysis_outputs/interval_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


@router.get("/analysis/round_summary_combined")
async def round_summary_combined(
    group_id: str = Query(...),
    round_index: int = Query(...),
    start_time: str = Query(...),
    end_time: str = Query(...)
):
    """
    当前轮结束后手动触发，将所有 interval summary 汇总成完整一轮总结。
    """
    cache_key = f"{group_id}:{round_index}"
    interval_chunks = interval_summary_cache.get(cache_key, [])
    # 按用户分组，收集所有chunk的summary
    user_chunks = {}
    for chunk in interval_chunks:
        uid = chunk["user_id"]
        if uid not in user_chunks:
            user_chunks[uid] = []
        user_chunks[uid].append(chunk["summary"])

    members = []
    for user_id, summaries in user_chunks.items():
        # 可以进一步合并每个summary的level（取众数或平均等）
        behavioral_levels = [s.get("behavioral_level") for s in summaries]
        cognitive_levels = [s.get("cognitive_level") for s in summaries]
        attention_levels = [s.get("shared_attention") for s in summaries]

        def most_common_level(levels):
            return max(set(levels), key=levels.count) if levels else "未知"

        # 汇总
        member_summary = {
            "time_range": {
                "start": start_time,
                "end": end_time
            },
            "user_id": user_id,
            "round": round_index,
            "behavioral_level": most_common_level(behavioral_levels),
            "cognitive_level": most_common_level(cognitive_levels),
            "shared_attention": most_common_level(attention_levels),
            "suggestions": [
                "请尝试提高认知互动水平",
                "是否可以进一步聚焦相似页面"
            ],
            "anomalies": []
        }
        members.append(member_summary)

    # 汇总 group
    all_behaviors = [m["behavioral_level"] for m in members]
    all_cognition = [m["cognitive_level"] for m in members]
    all_attention = [m["shared_attention"] for m in members]
    def most_common_level(levels):
        return max(set(levels), key=levels.count) if levels else "未知"
    group_summary = {
        "time_range": {
            "start": start_time,
            "end": end_time
        },
        "user_id": "group",
        "round": round_index,
        "behavioral_level": most_common_level(all_behaviors),
        "cognitive_level": most_common_level(all_cognition),
        "shared_attention": most_common_level(all_attention),
        "suggestions": [
            "请尝试提高认知互动水平",
            "是否可以进一步聚焦相似页面"
        ]
    }

    return {
        "group_summary": group_summary,
        "members": members
    }