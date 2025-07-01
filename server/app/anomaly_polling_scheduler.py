from fastapi import APIRouter
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading
from datetime import datetime, timedelta

# APScheduler全局调度器
scheduler = BackgroundScheduler()
scheduler_lock = threading.Lock()
scheduler.start()
anomaly_polling_jobs = {}

router = APIRouter()

class GroupPollingRequest(BaseModel):
    group_id: str

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

def anomaly_polling_job(group_id):
    print(f"[AI异常分析轮询] group_id={group_id} 开始分析...")
    members = get_group_members_simple(group_id)
    try:
        from app.routes.analysis import get_anomaly_status, IntervalSummaryRequest, Member, CurrentUser
        import asyncio
        member_objs = [Member(id=m.get("user_id"), name=m.get("name", "未知成员")) for m in members]
        # 每次自动计算分析窗口：end_time=now，start_time=now-2min
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=2)
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        for user in members:
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
        print(f"[AI异常分析轮询] group_id={group_id} 导入或调用分析接口异常: {e}")

@router.post("/analysis/anomaly_polling/start")
def start_anomaly_polling(req: GroupPollingRequest):
    job_id = f"anomaly_polling_{req.group_id}"
    with scheduler_lock:
        if job_id in anomaly_polling_jobs:
            return {"message": "该小组轮询已在进行中"}
        job = scheduler.add_job(
            anomaly_polling_job,
            trigger=IntervalTrigger(minutes=2),
            args=[req.group_id],
            id=job_id,
            replace_existing=True
        )
        anomaly_polling_jobs[job_id] = job
    print(f"✅ 已为group_id={req.group_id}启动AI异常分析轮询，每2分钟一次。")
    return {"message": "已启动AI异常分析轮询", "group_id": req.group_id}

@router.post("/analysis/anomaly_polling/stop")
def stop_anomaly_polling(req: GroupPollingRequest):
    job_id = f"anomaly_polling_{req.group_id}"
    with scheduler_lock:
        job = anomaly_polling_jobs.pop(job_id, None)
        if job:
            job.remove()
            print(f"🛑 已停止group_id={req.group_id}的AI异常分析轮询。")
            return {"message": "已停止AI异常分析轮询", "group_id": req.group_id}
        else:
            return {"message": "未找到该小组的轮询任务", "group_id": req.group_id} 