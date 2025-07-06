from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import time
from datetime import timezone
import asyncio
from datetime import datetime

websocket_router = APIRouter()

# 存储 WebSocket 连接
connected_clients = {}  # group_id -> [websocket]
connected_users = {}    # user_id -> websocket
connection_metadata = {}  # user_id -> {last_heartbeat, connected_at}

@websocket_router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    """WebSocket 连接管理 - 组连接，无需心跳"""
    await websocket.accept()
    
    if group_id not in connected_clients:
        connected_clients[group_id] = []

    connected_clients[group_id].append(websocket)
    print(f"🔌 [WebSocket] 组{group_id}新连接建立，当前连接数: {len(connected_clients[group_id])}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 [WebSocket] 收到组{group_id}数据: {data}")

            try:
                received_data = json.loads(data)
                print(f"📩 [WebSocket] 组{group_id}收到消息: {received_data}")

            except json.JSONDecodeError:
                print(f"❌ [WebSocket] 组{group_id}消息解析失败: {data}")

    except WebSocketDisconnect:
        connected_clients[group_id].remove(websocket)
        if len(connected_clients[group_id]) == 0:
            del connected_clients[group_id]
        print(f"🔌 [WebSocket] 组{group_id}连接断开，剩余连接数: {len(connected_clients.get(group_id, []))}")

@websocket_router.websocket("/ws/user/{user_id}")
async def user_websocket_endpoint(websocket: WebSocket, user_id: str):
    """用户个人WebSocket连接管理 - 需要心跳维持长连接"""
    await websocket.accept()
    
    # 清理可能存在的旧连接
    if user_id in connected_users:
        print(f"⚠️ [WebSocket] 用户{user_id}已有连接，清理旧连接")
        try:
            await connected_users[user_id].close()
        except:
            pass
    
    connected_users[user_id] = websocket
    connection_metadata[user_id] = {
        "last_heartbeat": datetime.now(timezone.utc),
        "connected_at": datetime.now(timezone.utc)
    }
    
    print(f"🔌 [WebSocket] 用户{user_id}连接建立，开始心跳监控")
    print(f"📊 [WebSocket] 当前用户连接数: {len(connected_users)}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 [WebSocket] 收到用户{user_id}数据: {data}")

            try:
                received_data = json.loads(data)
                
                # 处理心跳消息
                if received_data.get("type") == "heartbeat":
                    # 确保用户元数据存在
                    if user_id not in connection_metadata:
                        connection_metadata[user_id] = {
                            "last_heartbeat": datetime.now(timezone.utc),
                            "connected_at": datetime.now(timezone.utc)
                        }
                        print(f"⚠️ [WebSocket] 用户{user_id}元数据缺失，已重新创建")
                    else:
                        connection_metadata[user_id]["last_heartbeat"] = datetime.now(timezone.utc)
                    
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                    print(f"💓 [WebSocket] 用户{user_id}心跳响应 (8秒间隔)")
                    continue
                
                print(f"📩 [WebSocket] 用户{user_id}收到消息: {received_data}")

            except json.JSONDecodeError:
                print(f"❌ [WebSocket] 用户{user_id}消息解析失败: {data}")

    except WebSocketDisconnect:
        if user_id in connected_users:
            del connected_users[user_id]
        if user_id in connection_metadata:
            del connection_metadata[user_id]
        print(f"🔌 [WebSocket] 用户{user_id}连接断开")
        print(f"📊 [WebSocket] 当前用户连接数: {len(connected_users)}")

async def push_agenda_stage(group_id: str, stage: int):
    """向当前小组所有客户端推送议程阶段变更"""
    if group_id in connected_clients:
        payload = json.dumps({
            "type": "agenda_stage_update",
            "stage": stage
        })
        for client in connected_clients[group_id]:
            try:
                await client.send_text(payload)
            except Exception as e:
                print(f"❌ [WebSocket] 推送议程阶段失败: {e}")
        print(f"📤 [WebSocket] 已向组{group_id}推送议程阶段: {stage}")

async def push_personal_share_message(user_id: str, from_user: str, detail_type: str, detail_status: str, group_id: str):
    """向指定用户推送Share异常消息 - 同时推送到PC和移动设备"""
    import time
    start_time = time.time()
    print(f"📤 [Share推送] 开始向用户{user_id}推送Share异常消息...")
    
    # 1. WebSocket推送到PC
    ws_success = False
    if user_id in connected_users:
        payload = json.dumps({
            "type": "share",
            "from_user": from_user,
            "detail_type": detail_type,
            "detail_status": detail_status,
            "group_id": group_id
        })
        try:
            await connected_users[user_id].send_text(payload)
            ws_success = True
            print(f"📤 [Share推送] WebSocket推送成功: {detail_type}, {detail_status}")
        except Exception as e:
            print(f"❌ [Share推送] WebSocket推送失败: {e}")
            # 连接可能已断开，清理连接
            if user_id in connected_users:
                del connected_users[user_id]
            if user_id in connection_metadata:
                del connection_metadata[user_id]
    else:
        print(f"⚠️ [Share推送] 用户{user_id}没有WebSocket连接")
    
    # 2. 极光推送到移动设备
    jpush_success = False
    try:
        from app.database import db
        from app.jpush_api import send_jpush_notification
        
        # 获取用户的device_token
        user_doc = db.collection("users_info").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            device_token = user_data.get("device_token")
            
            if device_token:
                # 获取发送者姓名
                from_user_doc = db.collection("users_info").document(from_user).get()
                from_user_name = "未知用户"
                if from_user_doc.exists:
                    from_user_data = from_user_doc.to_dict()
                    from_user_name = from_user_data.get("name", "未知用户")
                
                # 构建推送内容
                alert = f"{from_user_name}分享了异常信息：{detail_type}"
                extras = {
                    "type": "share",
                    "from_user": from_user,
                    "from_user_name": from_user_name,
                    "detail_type": detail_type,
                    "detail_status": detail_status,
                    "group_id": group_id,
                    "title": "组员异常分享",
                    "body": alert
                }
                
                # 发送极光推送
                result = send_jpush_notification(
                    alert=alert,
                    registration_id=device_token,
                    extras=extras
                )
                
                if result:
                    jpush_success = True
                    print(f"📱 [Share推送] 极光推送成功，用户: {from_user_name} → {user_data.get('name', '未知用户')}")
                else:
                    print(f"❌ [Share推送] 极光推送失败")
            else:
                print(f"⚠️ [Share推送] 用户{user_id}没有device_token")
        else:
            print(f"⚠️ [Share推送] 用户{user_id}信息不存在")
            
    except Exception as e:
        print(f"❌ [Share推送] 极光推送异常: {e}")
    
    # 3. 记录推送结果
    duration = time.time() - start_time
    if ws_success or jpush_success:
        print(f"✅ [Share推送] 用户{user_id}推送完成，耗时{duration:.2f}秒")
        print(f"   - WebSocket: {'✅' if ws_success else '❌'}")
        print(f"   - 极光推送: {'✅' if jpush_success else '❌'}")
    else:
        print(f"❌ [Share推送] 用户{user_id}推送失败，耗时{duration:.2f}秒")
        print(f"   - WebSocket: ❌")
        print(f"   - 极光推送: ❌")

async def push_anomaly_analysis_result(user_id: str, analysis_result: dict):
    """向指定用户推送异常分析结果"""
    start_time = time.time()
    print(f"📡 [WebSocket推送] 开始向用户{user_id}推送异常分析结果...")
    
    if user_id in connected_users:
        payload = json.dumps({
            "type": "anomaly_analysis",
            "data": analysis_result
        })
        try:
            await connected_users[user_id].send_text(payload)
            duration = time.time() - start_time
            print(f"📡 [WebSocket推送] 向用户{user_id}推送异常分析结果成功，耗时{duration:.2f}秒")
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ [WebSocket推送] 向用户{user_id}推送失败，耗时{duration:.2f}秒: {e}")
            # 连接可能已断开，清理连接
            if user_id in connected_users:
                del connected_users[user_id]
            if user_id in connection_metadata:
                del connection_metadata[user_id]
    else:
        duration = time.time() - start_time
        print(f"⚠️ [WebSocket推送] 用户{user_id}没有WebSocket连接，无法推送异常分析结果，耗时{duration:.2f}秒")

# 心跳检查任务
async def heartbeat_checker():
    """定期检查WebSocket连接状态 - 适配8秒心跳间隔"""
    while True:
        try:
            current_time = datetime.now(timezone.utc)
            disconnected_users = []
            
            for user_id, metadata in connection_metadata.items():
                time_since_heartbeat = (current_time - metadata["last_heartbeat"]).total_seconds()
                if time_since_heartbeat > 48:  # 48秒无心跳（6个心跳周期）
                    print(f"⏰ [WebSocket] 用户{user_id}心跳超时({time_since_heartbeat:.1f}秒)，标记为断开")
                    disconnected_users.append(user_id)
            
            # 清理断开的连接
            for user_id in disconnected_users:
                if user_id in connected_users:
                    del connected_users[user_id]
                if user_id in connection_metadata:
                    del connection_metadata[user_id]
            
            if disconnected_users:
                print(f"🧹 [WebSocket] 清理了{len(disconnected_users)}个断开的连接")
                print(f"📊 [WebSocket] 当前活跃用户连接数: {len(connected_users)}")
            
        except Exception as e:
            print(f"❌ [WebSocket] 心跳检查出错: {e}")
        
        await asyncio.sleep(48)  # 每48秒检查一次（适配8秒心跳）

# 启动心跳检查任务
@websocket_router.on_event("startup")
async def start_heartbeat_checker():
    """启动心跳检查任务"""
    asyncio.create_task(heartbeat_checker())
    print("💓 [WebSocket] 心跳检查任务已启动 (48秒检查间隔，适配8秒心跳)")

@websocket_router.get("/websocket/status")
async def get_websocket_status():
    """获取WebSocket连接状态"""
    current_time = datetime.now(timezone.utc)
    
    # 统计用户连接信息
    user_connections = []
    for user_id, metadata in connection_metadata.items():
        time_since_heartbeat = (current_time - metadata["last_heartbeat"]).total_seconds()
        time_since_connected = (current_time - metadata["connected_at"]).total_seconds()
        
        user_connections.append({
            "user_id": user_id,
            "connected_at": metadata["connected_at"].strftime('%Y-%m-%d %H:%M:%S'),
            "last_heartbeat": metadata["last_heartbeat"].strftime('%Y-%m-%d %H:%M:%S'),
            "time_since_heartbeat_seconds": round(time_since_heartbeat, 1),
            "time_since_connected_seconds": round(time_since_connected, 1),
            "status": "active" if time_since_heartbeat < 48 else "timeout"  # 48秒超时
        })
    
    # 统计组连接信息
    group_connections = []
    for group_id, clients in connected_clients.items():
        group_connections.append({
            "group_id": group_id,
            "client_count": len(clients),
            "status": "active"
        })
    
    status_info = {
        "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "total_user_connections": len(connected_users),
        "total_group_connections": len(connected_clients),
        "user_connections": user_connections,
        "group_connections": group_connections
    }
    
    print(f"📊 [WebSocket状态] 用户连接数: {len(connected_users)}, 组连接数: {len(connected_clients)}")
    for conn in user_connections:
        print(f"   - 用户{conn['user_id']}: 心跳间隔{conn['time_since_heartbeat_seconds']}秒, 状态{conn['status']}")
    
    return status_info