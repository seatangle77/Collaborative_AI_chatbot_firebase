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
from app.jpush_api import send_jpush_notification

router = APIRouter()

class Member(BaseModel):
    id: str
    name: str

class CurrentUser(BaseModel):
    user_id: str
    name: str
    device_token: str

class IntervalSummaryRequest(BaseModel):
    group_id: str
    round_index: int
    start_time: str
    end_time: str
    members: List[Member]
    current_user: CurrentUser  # 前端直接传入当前用户信息


# 替换为 POST 方法，参数结构同 IntervalSummaryRequest，通过请求体接收
@router.post("/analysis/anomalies")
async def get_anomaly_status(req: IntervalSummaryRequest):
    import time
    total_start_time = time.time()
    print(f"🚀 [异常分析] 开始分析group_id={req.group_id}，用户={req.current_user.name}...")
    
    members = [{"user_id": m.id, "name": m.name} for m in req.members]

    # 阶段1: 数据预处理
    stage1_start = time.time()
    raw_data = extract_chunk_data_anomaly(
        group_id=req.group_id,
        round_index=req.round_index,
        start_time=req.start_time,
        end_time=req.end_time,
        member_list=members,
        current_user=req.current_user.dict()
    )
    stage1_duration = time.time() - stage1_start
    print(f"📊 [异常分析] 阶段1-数据预处理完成，耗时{stage1_duration:.2f}秒")
    
    # 阶段2: AI分析
    stage2_start = time.time()
    result = analyze_all_anomalies(raw_data)
    stage2_duration = time.time() - stage2_start
    print(f"🤖 [异常分析] 阶段2-AI分析完成，耗时{stage2_duration:.2f}秒")
    
    # 阶段3: 结果解析
    stage3_start = time.time()
    # 解析AI返回的JSON结果
    import re
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
                        should_push = (state_score < 25 or state_score > 75) or (content_similarity_score < 50)
                        print(f"📊 [异常分析] 状态评分：{state_score}，内容相似度评分：{content_similarity_score}，推送阈值：状态评分<25或>75，内容相似度评分<50，是否推送：{should_push}")
                    else:
                        should_push = True  # 如果没有评分信息，默认推送
                        print(f"⚠️ [异常分析] 未找到完整评分信息，默认推送")
                else:
                    should_push = False  # 如果没有score信息，默认不推送
                    print(f"⚠️ [异常分析] 未找到评分信息，默认不推送")
            else:
                glasses_summary = "你当前状态需要关注"
                should_push = True
        else:
            glasses_summary = "你当前状态需要关注"
            should_push = True
    except Exception as e:
        print("解析AI响应失败：", e)
        glasses_summary = "你当前状态需要关注"
        should_push = True
    stage3_duration = time.time() - stage3_start
    print(f"📝 [异常分析] 阶段3-结果解析完成，耗时{stage3_duration:.2f}秒")
    
    # 阶段4: 文件存储
    stage4_start = time.time()
    # 保存分析结果为文件
    import uuid
    from datetime import datetime
    from datetime import timezone
    os.makedirs("analysis_outputs", exist_ok=True)
    file_name = f"analysis_outputs/anomaly_{uuid.uuid4()}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    stage4_duration = time.time() - stage4_start
    print(f"💾 [异常分析] 阶段4-文件存储完成，耗时{stage4_duration:.2f}秒")

    # 阶段5: 数据库存储
    stage5_start = time.time()
    # 新建 anomaly_analysis_files 表并插入内容
    from app.database import db
    file_id = str(uuid.uuid4())
    db.collection("anomaly_raw_json_input").document(file_id).set({
        "id": file_id,
        "group_id": req.group_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": result  # 完整分析内容
    })

    # 新建anomaly_analysis_results表并插入数据
    analysis_id = str(uuid.uuid4())
    db.collection("anomaly_analysis_results").document(analysis_id).set({
        "id": analysis_id,
        "group_id": req.group_id,
        "start_time": req.start_time,
        "end_time": req.end_time,
        "current_user": req.current_user.dict(),
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
    print(f"🗄️ [异常分析] 阶段5-数据库存储完成，耗时{stage5_duration:.2f}秒")

    # 阶段6: 推送通知
    stage6_start = time.time()
    # 使用前端传入的当前用户信息发送推送通知
    current_user = req.current_user
    device_token = current_user.device_token
    
    # 构造返回给前端的数据
    response_data = {
        "raw_response": result.get("raw_response"),
        "summary": summary,
        "glasses_summary": glasses_summary,
        "detail": detail,
        "user_data_summary": user_data_summary,
        "more_info": more_info,
        "score": score,
        "should_push": should_push,
        "current_user": req.current_user.dict(),
        "group_id": req.group_id,
        "start_time": req.start_time,
        "end_time": req.end_time,
        "analysis_id": analysis_id,
        "anomaly_analysis_results_id": analysis_id  # 添加兼容字段
    }
    
    print(f"🔍 [调试] 推送数据中的ID字段:")
    print(f"  - analysis_id: {analysis_id}")
    print(f"  - anomaly_analysis_results_id: {analysis_id}")
    
    # 根据评分决定是否推送通知
    if should_push and device_token:
        # JPush 推送 - 使用眼镜版本
        send_jpush_notification(
            alert=glasses_summary,  # 直接使用眼镜版本作为推送内容
            registration_id=device_token,
            extras={
                "type": "anomaly",
                "title": "异常提醒",
                "body": glasses_summary,  # 眼镜版本
                "summary": summary or result.get("summary", "暂无摘要"),
                "suggestion": (detail or {}).get("suggestion", "") if detail else result.get("detail", {}).get("suggestion", ""),
                "user_id": current_user.user_id,
                "user_name": current_user.name
            }
        )
        print(f"✅ [异常分析] JPush推送完成，用户 {current_user.name}({current_user.user_id})")
        print(f"📱 [异常分析] 眼镜显示内容：{glasses_summary}")
    elif not should_push:
        print(f"⏭️ [异常分析] 评分不足70分，跳过推送，用户 {current_user.name}({current_user.user_id})")
    else:
        print(f"⚠️ [异常分析] 用户 {current_user.name}({current_user.user_id}) 未提供 device_token")

    # WebSocket 推送 - 向PC页面推送完整分析结果（无论评分如何都推送）
    try:
        from app.websocket_routes import push_anomaly_analysis_result
        await push_anomaly_analysis_result(current_user.user_id, response_data)
        print(f"📡 [异常分析] WebSocket推送完成，用户 {current_user.name}({current_user.user_id})")
    except Exception as e:
        print(f"⚠️ [异常分析] WebSocket推送失败: {e}")
    
    stage6_duration = time.time() - stage6_start
    print(f"📤 [异常分析] 阶段6-推送通知完成，耗时{stage6_duration:.2f}秒")

    total_duration = time.time() - total_start_time
    print(f"✅ [异常分析] group_id={req.group_id}，用户={req.current_user.name}分析完成，总耗时{total_duration:.2f}秒")

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
        "current_user": req.current_user.dict(),
        "group_id": req.group_id,
        "start_time": req.start_time,
        "end_time": req.end_time,
        "analysis_id": analysis_id,
        "anomaly_analysis_results_id": analysis_id  # 添加兼容字段
    }


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
    file_name = f"analysis_outputs/interval_{uuid.uuid4()}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
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

@router.get("/analysis/anomaly_results_by_user")
async def get_anomaly_results_by_user(
    user_id: str = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数，最大100")
):
    from app.database import db
    
    try:
        # 先获取所有匹配的文档（不排序）
        base_query = db.collection("anomaly_analysis_results") \
            .where("current_user.user_id", "==", user_id)
        
        # 获取总数
        total_docs = list(base_query.stream())
        total = len(total_docs)
        
        # 在内存中排序和分页
        sorted_docs = sorted(total_docs, key=lambda doc: doc.get("created_at") or "", reverse=True)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取分页数据
        paginated_docs = sorted_docs[offset:offset + page_size]
        data = [doc.to_dict() for doc in paginated_docs]
        
        return {
            "results": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        print(f"查询异常分析结果失败: {e}")
        # 返回空结果而不是抛出异常
        return {
            "results": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }