from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading
from datetime import datetime, timedelta, timezone
import time

# APScheduler全局调度器
scheduler = BackgroundScheduler()
scheduler_lock = threading.Lock()
scheduler.start()
anomaly_polling_jobs = {}  # job_id: job
execution_history = {}  # job_id: [execution_times] - 存储任务执行历史

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
    import time
    start_time = time.time()
    print(f"🔍 [成员查询] 开始查询group_id={group_id}的成员信息...")
    
    from app.database import db
    
    # 查询组成员关系
    query1_start = time.time()
    members_ref = db.collection("group_memberships").where("group_id", "==", group_id).stream()
    members = [doc.to_dict() for doc in members_ref]
    query1_duration = time.time() - query1_start
    print(f"📋 [成员查询] 查询组成员关系完成，耗时{query1_duration:.2f}秒，找到{len(members)}个成员关系")
    
    user_ids = [m["user_id"] for m in members]
    users_info = []
    
    # 查询用户详细信息
    query2_start = time.time()
    for uid in user_ids:
        user_doc = db.collection("users_info").document(uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data["user_id"] = uid
            users_info.append(user_data)
    query2_duration = time.time() - query2_start
    print(f"👥 [成员查询] 查询用户详细信息完成，耗时{query2_duration:.2f}秒，获取到{len(users_info)}个用户信息")
    
    total_duration = time.time() - start_time
    print(f"✅ [成员查询] group_id={group_id}成员查询完成，总耗时{total_duration:.2f}秒")
    
    return users_info

# 只分析单个成员
def anomaly_polling_job(group_id, user_id, interval_minutes=2):
    import time
    total_start_time = time.time()
    current_time = datetime.now(timezone.utc)
    
    # 记录任务执行历史（用于监控间隔变化）
    job_id = f"anomaly_polling_{group_id}_{user_id}"
    if job_id not in execution_history:
        execution_history[job_id] = []
    
    # 计算与上次执行的时间间隔
    last_execution = execution_history[job_id][-1] if execution_history[job_id] else None
    if last_execution:
        time_since_last = current_time - last_execution
        time_since_last_minutes = time_since_last.total_seconds() / 60
        print(f"⏱️ [AI异常分析轮询] 距离上次执行: {time_since_last_minutes:.1f}分钟 (预期: {interval_minutes}分钟)")
        if abs(time_since_last_minutes - interval_minutes) > 0.5:  # 允许0.5分钟的误差
            print(f"⚠️ [AI异常分析轮询] 时间间隔异常！预期{interval_minutes}分钟，实际{time_since_last_minutes:.1f}分钟")
    
    # 记录本次执行时间
    execution_history[job_id].append(current_time)
    # 只保留最近10次执行记录
    if len(execution_history[job_id]) > 10:
        execution_history[job_id] = execution_history[job_id][-10:]
    
    print(f"🚀 [AI异常分析轮询] group_id={group_id} user_id={user_id} 开始分析...")
    print(f"📅 [AI异常分析轮询] 任务执行时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ [AI异常分析轮询] 当前分析间隔: {interval_minutes}分钟")
    print(f"📊 [AI异常分析轮询] 历史执行次数: {len(execution_history[job_id])}")
    
    # 阶段1: 获取成员信息
    stage1_start = time.time()
    members = get_group_members_simple(group_id)
    user = next((m for m in members if m["user_id"] == user_id), None)
    if not user:
        print(f"❌ [AI异常分析轮询] group_id={group_id} user_id={user_id} 未找到成员，跳过。")
        return
    stage1_duration = time.time() - stage1_start
    print(f"📊 [AI异常分析轮询] 阶段1-获取成员信息完成，耗时{stage1_duration:.2f}秒")
    
    try:
        # 阶段2: 导入依赖
        stage2_start = time.time()
        from app.routes.analysis import get_anomaly_status, IntervalSummaryRequest, Member, CurrentUser
        import asyncio
        stage2_duration = time.time() - stage2_start
        print(f"📦 [AI异常分析轮询] 阶段2-导入依赖完成，耗时{stage2_duration:.2f}秒")
        
        # 阶段3: 准备请求数据
        stage3_start = time.time()
        member_objs = [Member(id=m.get("user_id"), name=m.get("name", "未知成员")) for m in members]
        # 自动计算分析窗口：end_time=now，start_time=now-interval_minutes
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=interval_minutes)
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"🕐 [AI异常分析轮询] 分析时间窗口: {start_time_str} ~ {end_time_str}")
        print(f"📏 [AI异常分析轮询] 分析窗口长度: {interval_minutes}分钟")
        
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
        stage3_duration = time.time() - stage3_start
        print(f"📋 [AI异常分析轮询] 阶段3-准备请求数据完成，耗时{stage3_duration:.2f}秒")
        
        # 阶段4: 调用分析接口
        stage4_start = time.time()
        try:
            result = asyncio.run(get_anomaly_status(req))
            stage4_duration = time.time() - stage4_start
            print(f"🤖 [AI异常分析轮询] 阶段4-AI分析完成，耗时{stage4_duration:.2f}秒。结果：", str(result)[:100])
        except Exception as e:
            stage4_duration = time.time() - stage4_start
            print(f"❌ [AI异常分析轮询] 阶段4-AI分析异常，耗时{stage4_duration:.2f}秒: {e}")
    except Exception as e:
        print(f"❌ [AI异常分析轮询] group_id={group_id} user_id={user_id} 导入或调用分析接口异常: {e}")
    
    total_duration = time.time() - total_start_time
    print(f"✅ [AI异常分析轮询] group_id={group_id} user_id={user_id} 分析完成，总耗时{total_duration:.2f}秒")

@router.post("/analysis/anomaly_polling/start")
def start_anomaly_polling(req: GroupPollingRequest):
    start_time = time.time()
    print(f"🚀 [轮询启动] 开始为group_id={req.group_id}启动异常分析轮询...")
    print(f"📅 [轮询启动] 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 [轮询启动] 调度器状态: {'运行中' if scheduler.running else '未运行'}")
    
    # 确保调度器正在运行
    if not scheduler.running:
        print("⚠️ [轮询启动] 调度器未运行，正在启动...")
        scheduler.start()
        print("✅ [轮询启动] 调度器已启动")
    
    members = get_group_members_simple(req.group_id)
    print(f"📊 [轮询启动] 获取到{len(members)}个成员")
    
    started = []
    with scheduler_lock:
        for user in members:
            user_id = user["user_id"]
            job_id = f"anomaly_polling_{req.group_id}_{user_id}"
            if job_id in anomaly_polling_jobs:
                print(f"⏭️ [轮询启动] 用户{user_id}已有任务，跳过")
                continue  # 已有任务
            
            # 计算下次执行时间（等待完整间隔）
            now = datetime.now(timezone.utc)
            next_run = now + timedelta(minutes=2)  # 2分钟后执行第一次
            
            job = scheduler.add_job(
                anomaly_polling_job,
                trigger=IntervalTrigger(minutes=2, start_date=next_run),
                args=[req.group_id, user_id, 2],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=300  # 5分钟宽限时间
            )
            anomaly_polling_jobs[job_id] = job
            started.append(user_id)
            next_run = job.next_run_time
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
            print(f"✅ [轮询启动] 为用户{user_id}创建定时任务成功，下次执行时间: {next_run_str}")
    
    # 打印所有活跃任务信息
    print(f"📋 [轮询启动] 当前活跃任务数量: {len(anomaly_polling_jobs)}")
    for job_id, job in anomaly_polling_jobs.items():
        next_run = job.next_run_time
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
        print(f"   - {job_id}: 下次执行时间 {next_run_str}")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ [轮询启动] 完成！耗时{duration:.2f}秒，已为group_id={req.group_id}的所有成员启动AI异常分析轮询，每2分钟一次。")
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
    import time
    start_time = time.time()
    print(f"⏱️ [间隔调整] 开始调整用户{req.user_id}的轮询间隔...")
    print(f"📅 [间隔调整] 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 [间隔调整] 新间隔: {req.interval_minutes}分钟")
    
    job_id = f"anomaly_polling_{req.group_id}_{req.user_id}"
    from app.database import db
    from datetime import datetime
    
    # 获取当前任务信息
    current_job = anomaly_polling_jobs.get(job_id)
    old_interval = None
    if current_job:
        old_interval = current_job.trigger.interval.total_seconds() / 60
        print(f"📊 [间隔调整] 当前间隔: {old_interval}分钟")
        print(f"📊 [间隔调整] 间隔变化: {old_interval}分钟 → {req.interval_minutes}分钟")
    
    # 记录Less点击事件
    less_click_id = f"{req.group_id}_{req.user_id}_{int(datetime.now(timezone.utc).timestamp())}"
    db.collection("feedback_clicks").document(less_click_id).set({
        "id": less_click_id,
        "group_id": req.group_id,
        "user_id": req.user_id,
        "anomaly_analysis_results_id": getattr(req, "anomaly_analysis_results_id", None),
        "clicked_at": datetime.now(timezone.utc).isoformat()
    })
    print(f"💾 [间隔调整] 已记录反馈点击事件")
    
    with scheduler_lock:
        # 先移除原有任务（如有）
        old_job = anomaly_polling_jobs.pop(job_id, None)
        if old_job:
            old_job.remove()
            print(f"🗑️ [间隔调整] 已移除原有任务")
        
        # 新建任务，使用新的interval_minutes
        now = datetime.now(timezone.utc)
        next_run = now + timedelta(minutes=req.interval_minutes)  # 等待完整间隔后执行
        
        job = scheduler.add_job(
            anomaly_polling_job,
            trigger=IntervalTrigger(minutes=req.interval_minutes, start_date=next_run),
            args=[req.group_id, req.user_id, req.interval_minutes],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=300
        )
        anomaly_polling_jobs[job_id] = job
        
        next_run = job.next_run_time
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
        print(f"✅ [间隔调整] 新任务创建成功，下次执行时间: {next_run_str}")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ [间隔调整] 完成！耗时{duration:.2f}秒，已为group_id={req.group_id} user_id={req.user_id}设置AI异常分析轮询周期为{req.interval_minutes}分钟。")
    return {"message": "已设置成员轮询周期", "group_id": req.group_id, "user_id": req.user_id, "interval_minutes": req.interval_minutes}

@router.post("/analysis/anomaly_polling/feedback_click")
def feedback_click(req: FeedbackClickRequest, background_tasks: BackgroundTasks):
    import time
    start_time = time.time()
    print(f"🖱️ [反馈点击] 收到用户{req.user_id}的{req.click_type}点击...")
    print(f"📅 [反馈点击] 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    from app.database import db
    click_id = f"{req.group_id}_{req.user_id}_{int(datetime.now().timestamp())}"
    db.collection("feedback_clicks").document(click_id).set({
        "id": click_id,
        "group_id": req.group_id,
        "user_id": req.user_id,
        "click_type": req.click_type,
        "anomaly_analysis_results_id": req.anomaly_analysis_results_id,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "detail_type": req.detail_type,
        "detail_status": req.detail_status,
        "share_to_user_ids": req.share_to_user_ids
    })
    print(f"💾 [反馈点击] 已记录点击事件到数据库")
    
    # Less时自动调整轮询周期为3分钟
    if req.click_type == "Less":
        print(f"⏱️ [反馈点击] 检测到Less点击，准备调整轮询间隔为3分钟...")
        job_id = f"anomaly_polling_{req.group_id}_{req.user_id}"
        
        # 获取当前任务信息
        current_job = anomaly_polling_jobs.get(job_id)
        old_interval = None
        if current_job:
            old_interval = current_job.trigger.interval.total_seconds() / 60
            print(f"📊 [反馈点击] 当前间隔: {old_interval}分钟")
            print(f"📊 [反馈点击] 间隔变化: {old_interval}分钟 → 3分钟")
        
        with scheduler_lock:
            old_job = anomaly_polling_jobs.pop(job_id, None)
            if old_job:
                old_job.remove()
                print(f"🗑️ [反馈点击] 已移除原有任务")
            
            # 创建新任务，间隔为3分钟
            now = datetime.now(timezone.utc)
            next_run = now + timedelta(minutes=3)  # 3分钟后执行第一次
            
            job = scheduler.add_job(
                anomaly_polling_job,
                trigger=IntervalTrigger(minutes=3, start_date=next_run),
                args=[req.group_id, req.user_id, 3],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=300
            )
            anomaly_polling_jobs[job_id] = job
            
            next_run = job.next_run_time
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
            print(f"✅ [反馈点击] 新任务创建成功，间隔3分钟，下次执行时间: {next_run_str}")
    
    # Share时通过WebSocket推送
    if req.click_type == "Share" and req.share_to_user_ids:
        print(f"📤 [反馈点击] 检测到Share点击，准备推送消息...")
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
        print(f"📤 [反馈点击] 已添加{len(req.share_to_user_ids)}个推送任务")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ [反馈点击] 完成！耗时{duration:.2f}秒")
    return {"message": "反馈已记录"}

@router.get("/analysis/anomaly_polling/status")
def get_polling_status():
    """获取轮询任务状态"""
    import time
    current_time = datetime.now(timezone.utc)
    
    status_info = {
        "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "scheduler_running": scheduler.running,
        "total_jobs": len(anomaly_polling_jobs),
        "jobs": []
    }
    
    for job_id, job in anomaly_polling_jobs.items():
        next_run = job.next_run_time
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未知"
        time_until_next = None
        if next_run:
            time_diff = next_run - current_time
            time_until_next = f"{time_diff.total_seconds():.1f}秒"
        
        # 获取执行历史
        job_execution_history = []
        if job_id in execution_history:
            history = execution_history[job_id]
            for i, exec_time in enumerate(history[-5:]):  # 只显示最近5次
                job_execution_history.append({
                    "index": len(history) - 5 + i + 1,
                    "time": exec_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        job_info = {
            "job_id": job_id,
            "next_run_time": next_run_str,
            "time_until_next": time_until_next,
            "trigger": str(job.trigger),
            "current_interval_minutes": job.trigger.interval.total_seconds() / 60,
            "execution_history": job_execution_history
        }
        status_info["jobs"].append(job_info)
    
    print(f"📊 [状态检查] 调度器状态: {'运行中' if scheduler.running else '未运行'}")
    print(f"📊 [状态检查] 活跃任务数量: {len(anomaly_polling_jobs)}")
    for job_info in status_info["jobs"]:
        print(f"   - {job_info['job_id']}: 下次执行 {job_info['next_run_time']} (还有{job_info['time_until_next']})")
        print(f"     当前间隔: {job_info['current_interval_minutes']}分钟")
        if job_info['execution_history']:
            print(f"     最近执行: {job_info['execution_history'][-1]['time']}")
    
    return status_info

@router.post("/analysis/anomaly_polling/trigger_now")
def trigger_polling_now(req: GroupPollingRequest):
    """立即触发轮询任务（用于测试）"""
    import time
    start_time = time.time()
    print(f"🚀 [手动触发] 立即触发group_id={req.group_id}的异常分析轮询...")
    
    members = get_group_members_simple(req.group_id)
    print(f"📊 [手动触发] 获取到{len(members)}个成员")
    
    triggered = []
    for user in members:
        user_id = user["user_id"]
        print(f"🔧 [手动触发] 立即执行用户{user_id}的分析任务...")
        try:
            # 直接调用任务函数
            anomaly_polling_job(req.group_id, user_id, 2)
            triggered.append(user_id)
            print(f"✅ [手动触发] 用户{user_id}分析任务执行完成")
        except Exception as e:
            print(f"❌ [手动触发] 用户{user_id}分析任务执行失败: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ [手动触发] 完成！耗时{duration:.2f}秒，已触发{len(triggered)}个用户的分析任务。")
    return {"message": "已手动触发异常分析轮询", "group_id": req.group_id, "triggered_user_ids": triggered} 