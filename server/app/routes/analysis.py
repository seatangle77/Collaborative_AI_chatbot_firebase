import time
import traceback
from datetime import timedelta, datetime, timezone
from typing import Dict, Any, List

from fastapi import BackgroundTasks
from google.cloud.firestore_v1 import FieldFilter

from server.app.anomaly_analyze import local_analyze
from server.app.anomaly_polling_scheduler import start_analyze, stop_analyze
from server.app.anomaly_preprocessor import get_local_analyze_result, get_ai_analyze_result, \
    parse_iso_time
from server.app.database import db
from server.app.logger.logger_loader import logger
from server.app.websocket_routes import push_personal_share_message, push_anomaly_analysis_result

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
from server.app.jpush_api import jpush_personal_share_message, send_jpush_notification
import asyncio
from server.app.websocket_routes import push_stop_task, push_agenda_stage

router = APIRouter()

class IntervalSummaryRequest(BaseModel):
    group_id: str
    round_index: int
    start_time: str
    end_time: str

class GroupPollingRequest(BaseModel):
    group_id: str

class FeedbackClickRequest(BaseModel):
    group_id: str
    user_id: str
    click_type: str  # Less/More/Share
    anomaly_analysis_results_id: str = None
    detail_type: str = None
    detail_status: str = None
    share_to_user_ids: list = None

class PushAiAnalysisRequest(BaseModel):
    push_ji: bool
    device_token: str
    glasses_summary: str
    summary: str
    detail_suggestion: str
    user_id: str
    user_name: str
    push_pc: bool
    ai_analyze_result: dict


# 120秒的间隔
_default_interval_seconds = 120
# 用户定制自己的提示间隔时间，(user_id, interval_seconds)
_user_notify_interval_seconds = {}
# 用户最后一次通知时间
_user_notify_last_time = {}

# 替换为 POST 方法，参数结构同 IntervalSummaryRequest，通过请求体接收
@router.post("/analysis/anomalies")
async def get_anomaly_status(req: GroupPollingRequest):
    return get_local_analyze_result(req.group_id)

@router.post("/analysis/get_ai_analyze")
async def get_ai_analyze(req: GroupPollingRequest):
    return get_ai_analyze_result(req.group_id)

@router.post("/analysis/get_next_notify_ai_analyze_result")
async def get_next_notify_ai_analyze_result(req: GroupPollingRequest):
    global _user_notify_last_time, _user_notify_interval_seconds, _default_interval_seconds

    analyze_result = get_ai_analyze_result(req.group_id, limit=1)
    if len(analyze_result) > 0:
        last_ai_analyze_content = analyze_result[0]

        user_ids = list(last_ai_analyze_content.keys())
        end_time = last_ai_analyze_content.get("time_range",{}).get("end","")
        for user_id in user_ids:
            if user_id != "time_range":
                last_notify_time = _user_notify_last_time.get(user_id)
                interval_seconds = _user_notify_interval_seconds.get(user_id, _default_interval_seconds)
                if last_notify_time is None:
                    # 如果是第一次执行，用AI分析结果的时间作为下次通知时间
                    next_notify_time = parse_iso_time(end_time)
                    last_ai_analyze_content.get(user_id, {}).update({"last_notify_time": ""})
                else:
                    # 上一次通知时间+间隔时间作为下一次通知时间
                    next_notify_time = last_notify_time + timedelta(seconds=interval_seconds)
                    last_ai_analyze_content.get(user_id, {}).update({"last_notify_time": last_notify_time.isoformat()})

                last_ai_analyze_content.get(user_id, {}).update({"next_notify_time": next_notify_time.isoformat()})
                
        return last_ai_analyze_content
    else:
        return {}


@router.post("/analysis/push_ai_analyze_result")
async def push_ai_analyze_result(req: PushAiAnalysisRequest):
    global _user_notify_last_time
    _user_notify_last_time[req.user_id] = datetime.now(timezone.utc)

    # 根据评分决定是否推送通知
    try:
        if req.push_ji:
            # JPush 推送 - 使用眼镜版本
            send_jpush_notification(
                alert=req.glasses_summary,  # 直接使用眼镜版本作为推送内容
                registration_id=req.device_token,
                extras={
                    "type": "anomaly",
                    "title": "异常提醒",
                    "body": req.glasses_summary,  # 眼镜版本
                    "summary": req.summary,
                    "suggestion": req.detail_suggestion,
                    "user_id": req.user_id,
                    "user_name": req.user_name
                }
            )
            logger.info(f"✅ [异常分析] JPush推送完成，用户 {req.user_name}({req.user_id}) 眼镜显示内容：{req.glasses_summary}")
    except Exception as e:
        logger.error(f"⚠️ [异常分析] JPush推送失败: {traceback.format_exc()}")

    # WebSocket 推送 - 向PC页面推送完整分析结果
    try:
        if req.push_pc:
            logger.info(f"📡 [异常分析] 开始WebSocket推送，用户ID: {req.user_id}")
            await push_anomaly_analysis_result(req.user_id, req.ai_analyze_result)
            logger.info(f"✅ [异常分析] WebSocket推送完成，用户ID: {req.user_id}")
        else:
            logger.info(f"⏭️ [异常分析] 跳过WebSocket推送，push_pc: {req.push_pc}")
    except Exception as e:
        logger.error(f"⚠️ [异常分析] WebSocket推送失败: {traceback.format_exc()}")

    # 构造GroupPollingRequest来调用get_next_notify_ai_analyze_result
    # 从ai_analyze_result中提取group_id，如果没有则使用默认值
    group_id = req.ai_analyze_result.get('group_id', 'default_group')
    polling_req = GroupPollingRequest(group_id=group_id)
    return await get_next_notify_ai_analyze_result(polling_req)

# 新增：只执行本地分析的接口
@router.post("/analysis/local_anomalies")
async def get_realtime_local_anomaly_status(req: IntervalSummaryRequest):
    """
    只执行本地分析，不调用AI分析，直接返回本地分析结果
    """
    try:

        start_time = time.time()
        logger.info(f"🔍 [本地异常分析] 开始分析 group_id={req.group_id}")
        
        # 本地数据分析
        chunk_data_with_local_analyze, local_analyze_result = local_analyze(req.group_id, req.start_time, req.end_time, is_save_debug_info=False)

        processing_time = time.time() - start_time
        logger.info(f"📊 [本地异常分析] 分析完成，耗时{processing_time:.2f}秒")

        # 缓存本地分析结果
        if local_analyze_result:
            return {
                "local_analysis": local_analyze_result,
                "raw_data_summary": {
                    "time_range": chunk_data_with_local_analyze.get('time_range'),
                    "users_count": len(chunk_data_with_local_analyze.get('users', [])),
                    "speech_transcripts_count": len(chunk_data_with_local_analyze.get('raw_tables', {}).get('speech_transcripts', [])),
                    "note_edit_history_count": len(chunk_data_with_local_analyze.get('raw_tables', {}).get('note_edit_history', [])),
                    "pageBehaviorLogs_count": len(chunk_data_with_local_analyze.get('raw_tables', {}).get('pageBehaviorLogs', {}))
                },
                "processing_time": processing_time,
                "analysis_timestamp": time.time()
            }
        else:
            return {
                "local_analysis": None,
                "message": "用户活动数据增量为0，无法进行分析",
                "processing_time": time.time() - start_time
            }
        
    except Exception as e:
        logger.error(f"❌ [本地异常分析] 分析失败: {traceback.format_exc()}")
        return {
            "error": str(e),
            "local_analysis": None,
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0
        }


@router.get("/analysis/anomaly_results_by_user")
async def get_anomaly_results_by_user(
    group_id: str,
    user_id: str = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数，最大100")
):

    try:
        # 注意：由于数据库中实际没有存储 current_user 字段，这里暂时查询所有记录
        results = db.collection("anomaly_analysis_group_results") \
            .where(filter=FieldFilter("group_id", "==", group_id)) \
            .order_by("created_at", direction="DESCENDING") \
            .stream()

        # 获取总数
        ai_result_list = [doc.to_dict() for doc in results]
        total = len(ai_result_list)

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取分页数据
        paginated_docs = ai_result_list[offset:offset + page_size]
        return_list = []
        for doc in paginated_docs:
            raw_response = doc.get("raw_response", {})
            if isinstance(raw_response, dict):
                user_anomaly_result = raw_response.get(user_id, {})
                # 添加数据库记录的ID
                user_anomaly_result["record_id"] = doc.get("id", "")
                user_anomaly_result["start_time"] = doc.get("start_time", "")
                user_anomaly_result["end_time"] = doc.get("end_time", "")
                return_list.append(user_anomaly_result)

        return {
            "results": return_list,
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
    global _user_notify_interval_seconds, _user_notify_last_time
    _user_notify_interval_seconds = {}
    _user_notify_last_time = {}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, start_analyze, req.group_id)
    await push_agenda_stage(req.group_id, 1)
    return result


@router.post("/analysis/anomaly_polling/stop")
async def stop_anomaly_polling(req: GroupPollingRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, stop_analyze, req.group_id)
    await push_stop_task(req.group_id)
    return result

@router.post("/analysis/anomaly_polling/feedback_click")
def feedback_click(req: FeedbackClickRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    logger.info(f"🖱️ [反馈点击] 收到用户{req.user_id}的{req.click_type}点击...")

    # Less\More 时调整轮询周期
    global _default_interval_seconds, _user_notify_interval_seconds
    if req.click_type == "Less":
        old_interval = _user_notify_interval_seconds.get(req.user_id, _default_interval_seconds)

        if old_interval + 60 <= _default_interval_seconds * 2:
            _user_notify_interval_seconds[req.user_id] = old_interval + 60

        logger.info(
            f"📊 [反馈点击] 检测到Less点击，调整轮询间隔: {old_interval}s → {_user_notify_interval_seconds.get(req.user_id, _default_interval_seconds)}s")
    elif req.click_type == "More":
        old_interval = _user_notify_interval_seconds.get(req.user_id, _default_interval_seconds)

        if old_interval - 60 >= _default_interval_seconds:
            _user_notify_interval_seconds[req.user_id] = old_interval - 60

        logger.info(
            f"📊 [反馈点击] 检测到More点击，调整轮询间隔: {old_interval}s → {_user_notify_interval_seconds.get(req.user_id, _default_interval_seconds)}s")
    # Share时通过WebSocket推送
    elif req.click_type == "Share" and req.share_to_user_ids:
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

    click_id = f"{req.group_id}_{req.user_id}_{int(datetime.now().timestamp())}"
    feedback_setting = {
        "id": click_id,
        "group_id": req.group_id,
        "user_id": req.user_id,
        "click_type": req.click_type,
        "anomaly_analysis_results_id": req.anomaly_analysis_results_id,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "detail_type": req.detail_type,
        "detail_status": req.detail_status,
        "share_to_user_ids": req.share_to_user_ids,
        "interval_seconds": _user_notify_interval_seconds.get(req.user_id, _default_interval_seconds),
    }
    db.collection("feedback_clicks").document(click_id).set(feedback_setting)

    logger.info(f"✅ [反馈点击] 完成！耗时{(time.time() - start_time):.2f}秒")
    return {"message": "反馈已记录", "feedback_setting": feedback_setting}


