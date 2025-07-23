from typing import Dict, Any, List

from fastapi import BackgroundTasks

from server.app.anomaly_analyze import analyze_anomaly_status, Member, CurrentUser
from server.app.anomaly_polling_scheduler import feedback_setting, start_analyze, stop_analyze
from server.app.database import db
from server.app.logger.logger_loader import logger
from server.app.websocket_routes import push_personal_share_message

# 模拟缓存：用于暂存 interval summary 结果
interval_summary_cache: Dict[str, List[Dict[str, Any]]] = {}

# Firebase Admin SDK 导入与初始化
from firebase_admin import credentials, initialize_app
import firebase_admin

if not len(firebase_admin._apps):
    cred = credentials.Certificate("./server/firebase-key.json")
    initialize_app(cred)

from fastapi import APIRouter, Query
from pydantic import BaseModel
#
from server.app.jpush_api import jpush_personal_share_message

router = APIRouter()

class IntervalSummaryRequest(BaseModel):
    group_id: str
    round_index: int
    start_time: str
    end_time: str
    members: List[Member]
    current_user: CurrentUser  # 前端直接传入当前用户信息

class GroupPollingRequest(BaseModel):
    group_id: str

class MemberPollingRequest(BaseModel):
    group_id: str
    user_id: str
    interval_minutes: int
    anomaly_analysis_results_id: str = None

class FeedbackClickRequest(BaseModel):
    group_id: str
    user_id: str
    click_type: str  # Less/More/Share
    anomaly_analysis_results_id: str = None
    detail_type: str = None
    detail_status: str = None
    share_to_user_ids: list = None

# 替换为 POST 方法，参数结构同 IntervalSummaryRequest，通过请求体接收
@router.post("/analysis/anomalies")
async def get_anomaly_status(req: IntervalSummaryRequest):
    return analyze_anomaly_status(req.group_id, req.round_index, req.start_time, req.end_time,req.members, req.current_user)

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
        logger.info(f"查询异常分析结果失败: {e}")
        # 返回空结果而不是抛出异常
        return {
            "results": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }


@router.post("/analysis/anomaly_polling/start")
async def start_anomaly_polling(req: GroupPollingRequest):
    result = start_analyze(req.group_id)
    from server.app.websocket_routes import push_agenda_stage
    await push_agenda_stage(req.group_id, 1)
    return result


@router.post("/analysis/anomaly_polling/stop")
def stop_anomaly_polling(req: GroupPollingRequest):
    return stop_analyze(req.group_id)

@router.post("/analysis/anomaly_polling/feedback_click")
def feedback_click(req: FeedbackClickRequest, background_tasks: BackgroundTasks):
    feedback_setting(req.group_id, req.user_id, req.interval_minutes, req.anomaly_analysis_results_id,req.detail_type, req.detail_status, req.share_to_user_ids)
    
    # Share时通过WebSocket推送
    if req.click_type == "Share" and req.share_to_user_ids:
        logger.info(f"📤 [反馈点击] 检测到Share点击，准备推送消息...")

        for uid in req.share_to_user_ids:
            background_tasks.add_task(
                push_personal_share_message,
                user_id=uid,
                from_user=req.user_id,
                detail_type=req.detail_type,
                detail_status=req.detail_status,
                group_id=req.group_id
            )
            background_tasks.add_task(
                jpush_personal_share_message,
                user_id=uid,
                from_user=req.user_id,
                detail_type=req.detail_type,
                detail_status=req.detail_status,
                group_id=req.group_id
            )

        logger.info(f"📤 [反馈点击] 已添加{len(req.share_to_user_ids)}个推送任务")

    return {"message": "反馈已记录"}

