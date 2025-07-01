from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading
from datetime import datetime, timedelta

# APScheduler全局调度器
scheduler = BackgroundScheduler()
scheduler_lock = threading.Lock()
scheduler.start()
anomaly_polling_jobs = {}  # job_id: job

router = APIRouter()

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

def get_group_members_simple(group_id: str):
    from app.database import db
    members_ref = db.collection("group_memberships").where("group_id", "==", group_id).stream()
    members = [doc.to_dict() for doc in members_ref]
    user_ids = [m["user_id"] for m in members]
    users_info = []
    for uid in user_ids:
        user_doc = db.collection("users_info").document(uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data["user_id"] = uid
            users_info.append(user_data)
    return users_info

# 只分析单个成员
def anomaly_polling_job(group_id, user_id, interval_minutes=2):
    print(f"[AI异常分析轮询] group_id={group_id} user_id={user_id} 开始分析...")
    members = get_group_members_simple(group_id)
    user = next((m for m in members if m["user_id"] == user_id), None)
    if not user:
        print(f"[AI异常分析轮询] group_id={group_id} user_id={user_id} 未找到成员，跳过。")
        return
    try:
        from app.routes.analysis import get_anomaly_status, IntervalSummaryRequest, Member, CurrentUser
        import asyncio
        member_objs = [Member(id=m.get("user_id"), name=m.get("name", "未知成员")) for m in members]
        # 自动计算分析窗口：end_time=now，start_time=now-interval_minutes
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=interval_minutes)
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        current_user = CurrentUser(
            user_id=user.get("user_id"),
            name=user.get("name", "未知成员"),
            device_token=user.get("device_token", "")
        )
        req = IntervalSummaryRequest(
            group_id=group_id,
            round_index=1,  # 轮次可根据实际需要调整
            start_time=start_time_str,
            end_time=end_time_str,
            members=member_objs,
            current_user=current_user
        )
        try:
            result = asyncio.run(get_anomaly_status(req))
            print(f"[AI异常分析轮询] group_id={group_id} user={current_user.name} 分析完成。结果：", str(result)[:100])
        except Exception as e:
            print(f"[AI异常分析轮询] group_id={group_id} user={current_user.name} 分析异常: {e}")
    except Exception as e:
        print(f"[AI异常分析轮询] group_id={group_id} user_id={user_id} 导入或调用分析接口异常: {e}")

@router.post("/analysis/anomaly_polling/start")
def start_anomaly_polling(req: GroupPollingRequest):
    members = get_group_members_simple(req.group_id)
    started = []
    with scheduler_lock:
        for user in members:
            user_id = user["user_id"]
            job_id = f"anomaly_polling_{req.group_id}_{user_id}"
            if job_id in anomaly_polling_jobs:
                continue  # 已有任务
            job = scheduler.add_job(
                anomaly_polling_job,
                trigger=IntervalTrigger(minutes=2),
                args=[req.group_id, user_id, 2],
                id=job_id,
                replace_existing=True
            )
            anomaly_polling_jobs[job_id] = job
            started.append(user_id)
    print(f"✅ 已为group_id={req.group_id}的所有成员启动AI异常分析轮询，每2分钟一次。")
    return {"message": "已启动AI异常分析轮询", "group_id": req.group_id, "started_user_ids": started}

@router.post("/analysis/anomaly_polling/stop")
def stop_anomaly_polling(req: GroupPollingRequest):
    members = get_group_members_simple(req.group_id)
    stopped = []
    with scheduler_lock:
        for user in members:
            user_id = user["user_id"]
            job_id = f"anomaly_polling_{req.group_id}_{user_id}"
            job = anomaly_polling_jobs.pop(job_id, None)
            if job:
                job.remove()
                stopped.append(user_id)
    print(f"🛑 已停止group_id={req.group_id}的所有成员AI异常分析轮询。")
    return {"message": "已停止AI异常分析轮询", "group_id": req.group_id, "stopped_user_ids": stopped}

@router.post("/analysis/anomaly_polling/set_interval")
def set_anomaly_polling_interval(req: MemberPollingRequest):
    job_id = f"anomaly_polling_{req.group_id}_{req.user_id}"
    from app.database import db
    from datetime import datetime
    # 记录Less点击事件
    less_click_id = f"{req.group_id}_{req.user_id}_{int(datetime.now().timestamp())}"
    db.collection("feedback_clicks").document(less_click_id).set({
        "id": less_click_id,
        "group_id": req.group_id,
        "user_id": req.user_id,
        "anomaly_analysis_results_id": getattr(req, "anomaly_analysis_results_id", None),
        "clicked_at": datetime.now().isoformat()
    })
    with scheduler_lock:
        # 先移除原有任务（如有）
        old_job = anomaly_polling_jobs.pop(job_id, None)
        if old_job:
            old_job.remove()
        # 新建任务，使用新的interval_minutes
        job = scheduler.add_job(
            anomaly_polling_job,
            trigger=IntervalTrigger(minutes=req.interval_minutes),
            args=[req.group_id, req.user_id, req.interval_minutes],
            id=job_id,
            replace_existing=True
        )
        anomaly_polling_jobs[job_id] = job
    print(f"⏱️ 已为group_id={req.group_id} user_id={req.user_id}设置AI异常分析轮询周期为{req.interval_minutes}分钟。并记录Less点击。")
    return {"message": "已设置成员轮询周期", "group_id": req.group_id, "user_id": req.user_id, "interval_minutes": req.interval_minutes}

@router.post("/analysis/anomaly_polling/feedback_click")
def feedback_click(req: FeedbackClickRequest, background_tasks: BackgroundTasks):
    from app.database import db
    from datetime import datetime
    click_id = f"{req.group_id}_{req.user_id}_{int(datetime.now().timestamp())}"
    db.collection("feedback_clicks").document(click_id).set({
        "id": click_id,
        "group_id": req.group_id,
        "user_id": req.user_id,
        "click_type": req.click_type,
        "anomaly_analysis_results_id": req.anomaly_analysis_results_id,
        "clicked_at": datetime.now().isoformat(),
        "detail_type": req.detail_type,
        "detail_status": req.detail_status,
        "share_to_user_ids": req.share_to_user_ids
    })
    # Less时自动调整轮询周期为3分钟
    if req.click_type == "Less":
        job_id = f"anomaly_polling_{req.group_id}_{req.user_id}"
        with scheduler_lock:
            old_job = anomaly_polling_jobs.pop(job_id, None)
            if old_job:
                old_job.remove()
            job = scheduler.add_job(
                anomaly_polling_job,
                trigger=IntervalTrigger(minutes=3),
                args=[req.group_id, req.user_id, 3],
                id=job_id,
                replace_existing=True
            )
            anomaly_polling_jobs[job_id] = job
        print(f"⏱️ 已为group_id={req.group_id} user_id={req.user_id}设置AI异常分析轮询周期为3分钟（Less点击）")
    # Share时通过WebSocket推送
    if req.click_type == "Share" and req.share_to_user_ids:
        from app.websocket_routes import push_personal_share_message
        for uid in req.share_to_user_ids:
            background_tasks.add_task(
                push_personal_share_message,
                user_id=uid,
                from_user=req.user_id,
                detail_type=req.detail_type,
                detail_status=req.detail_status,
                group_id=req.group_id
            )
    return {"message": "反馈已记录"} 