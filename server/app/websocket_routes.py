import queue
import threading
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import time
from datetime import timezone
import asyncio
from datetime import datetime

from server.app.logger.logger_loader import logger

websocket_router = APIRouter()

# 存储 WebSocket 连接
connected_users = {}    # user_id -> websocket
connection_metadata = {}  # user_id -> {last_heartbeat, connected_at}

_handle_interval = 0.01
_send_interval = 0.01
_queue_size = 1000
_received_q = queue.Queue(_queue_size)
_send_q = queue.Queue(_queue_size)

@websocket_router.websocket("/ws/user/{user_id}")
async def user_websocket_endpoint(websocket: WebSocket, user_id: str):
    """用户个人WebSocket连接管理 - 需要心跳维持长连接"""
    await websocket.accept()
    
    # 清理可能存在的旧连接
    if user_id in connected_users:
        logger.info(f"⚠️ [WebSocket] 用户{user_id}已有连接，清理旧连接")
        try:
            await connected_users[user_id].close()
        except:
            pass
    
    connected_users[user_id] = websocket
    connection_metadata[user_id] = {
        "last_heartbeat": datetime.now(timezone.utc),
        "connected_at": datetime.now(timezone.utc)
    }
    
    logger.info(f"🔌 [WebSocket] 用户{user_id}连接建立，开始心跳监控")
    logger.info(f"📊 [WebSocket] 当前用户连接数: {len(connected_users)}")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"📩 [WebSocket] 收到用户{user_id}数据: {data}")

            try:
                received_data = json.loads(data)

                # 写入队列，异步处理
                _received_q.put((user_id,received_data))

            except json.JSONDecodeError:
                logger.info(f"❌ [WebSocket] 用户{user_id}消息解析失败: {data}")

    except WebSocketDisconnect:
        if user_id in connected_users:
            del connected_users[user_id]
        if user_id in connection_metadata:
            del connection_metadata[user_id]
        logger.info(f"🔌 [WebSocket] 用户{user_id}连接断开")
        logger.info(f"📊 [WebSocket] 当前用户连接数: {len(connected_users)}")

async def _message_handler():
    logger.info(f'Start websocket server (_message_handler). TID={threading.get_native_id()}.')
    """执行接收到的指令."""
    while True:
        try:
            await asyncio.sleep(_handle_interval)
            while not _received_q.empty():
                user_id,received_data = _received_q.get()

                # 处理心跳消息
                if received_data.get("type") == "heartbeat":
                    # 确保用户元数据存在
                    if user_id not in connection_metadata:
                        connection_metadata[user_id] = {
                            "last_heartbeat": datetime.now(timezone.utc),
                            "connected_at": datetime.now(timezone.utc)
                        }
                        logger.info(f"⚠️ [WebSocket] 用户{user_id}元数据缺失，已重新创建")
                    else:
                        connection_metadata[user_id]["last_heartbeat"] = datetime.now(timezone.utc)

                    _send_q.put((user_id, json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })))
                    logger.info(f"💓 [WebSocket] 用户{user_id}心跳响应 (8秒间隔)")
                else:
                    logger.info(f"📩 [WebSocket] 用户{user_id}收到消息: {received_data}")

        except (Exception, ):
            logger.error('Error in _message_handler loop: %s' % traceback.format_exc())

async def _sender():
    logger.info(f'Start websocket server (_sender). TID={threading.get_native_id()}.')
    while True:
        user_id = None
        try:
            await asyncio.sleep(_handle_interval)
            while not _send_q.empty():
                user_id,send_data = _send_q.get()
                if user_id is not None:
                    if user_id not in connected_users:
                        logger.error(f"[WebSocket] 用户{user_id}连接不存在，消息推送失败。{send_data}")
                        continue
                    user_ws = connected_users[user_id]
                    await user_ws.send_text(send_data)
                else:
                    # 全员推送
                    for user_ws in connected_users.values():
                        await user_ws.send_text(send_data)
        except (Exception, ):
            logger.error('Error in _sender loop: %s' % traceback.format_exc())
            # 连接可能已断开，清理连接
            if user_id is not None and user_id in connected_users:
                del connected_users[user_id]
            if user_id is not None and user_id in connection_metadata:
                del connection_metadata[user_id]

# 心跳检查任务
async def heartbeat_checker():
    logger.info(f'Start websocket server (heartbeat_checker). TID={threading.get_native_id()}.')
    """定期检查WebSocket连接状态 - 适配8秒心跳间隔"""
    while True:
        try:
            current_time = datetime.now(timezone.utc)
            disconnected_users = []
            
            for user_id, metadata in connection_metadata.items():
                time_since_heartbeat = (current_time - metadata["last_heartbeat"]).total_seconds()
                if time_since_heartbeat > 48:  # 48秒无心跳（6个心跳周期）
                    logger.info(f"⏰ [WebSocket] 用户{user_id}心跳超时({time_since_heartbeat:.1f}秒)，标记为断开")
                    disconnected_users.append(user_id)
            
            # 清理断开的连接
            for user_id in disconnected_users:
                if user_id in connected_users:
                    del connected_users[user_id]
                if user_id in connection_metadata:
                    del connection_metadata[user_id]
            
            if disconnected_users:
                logger.info(f"🧹 [WebSocket] 清理了{len(disconnected_users)}个断开的连接")
                logger.info(f"📊 [WebSocket] 当前活跃用户连接数: {len(connected_users)}")
            
        except Exception as e:
            logger.info(f"❌ [WebSocket] 心跳检查出错: {e}")
        
        await asyncio.sleep(48)  # 每48秒检查一次（适配8秒心跳）

first_startup = False
# 启动任务
@websocket_router.on_event("startup")
async def start_heartbeat_checker():
    """启动心跳检查任务"""
    global first_startup
    if not first_startup:
        asyncio.create_task(heartbeat_checker())
        asyncio.create_task(_message_handler())
        asyncio.create_task(_sender())
        first_startup = True


async def push_agenda_stage(group_id: str, stage: int):
    """向当前小组所有客户端推送议程阶段变更"""
    payload = json.dumps({
        "type": "agenda_stage_update",
        "stage": stage
    })
    _send_q.put((None, payload))
    logger.info(f"📤 [WebSocket] 已向组{group_id}推送议程阶段: {stage}")

async def push_stop_task(group_id: str):
    """向当前小组所有客户端广播停止任务指令"""
    payload = json.dumps({
        "type": "stop_task",
        "group_id": group_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    _send_q.put((None, payload))
    logger.info(f"📤 [WebSocket] 已向组{group_id}广播停止任务指令")


async def push_personal_share_message(user_id: str, from_user: str, detail_type: str, detail_status: str,
                                      group_id: str):
    """向指定用户推送Share异常消息 - 同时推送到PC和移动设备"""
    start_time = time.time()
    logger.info(f"📤 [Share推送] 开始向用户{user_id}推送Share异常消息...")

    # 1. WebSocket推送到PC
    payload = json.dumps({
        "type": "share",
        "from_user": from_user,
        "detail_type": detail_type,
        "detail_status": detail_status,
        "group_id": group_id
    })
    _send_q.put((user_id, payload))
    logger.info(f"📤 [Share推送] WebSocket推送: {detail_type}, {detail_status}")


async def push_anomaly_analysis_result(user_id: str, analysis_result: dict):
    """向指定用户推送异常分析结果"""
    logger.info(f"📡 [WebSocket推送] 开始向用户{user_id}推送异常分析结果...")
    payload = json.dumps({
        "type": "anomaly_analysis",
        "data": analysis_result
    })
    _send_q.put((user_id, payload))

async def push_peer_prompt_received(user_id: str, prompt_data: dict):
    """
    向指定用户推送Peer Prompt接收消息
    :param user_id: 接收者用户ID
    :param prompt_data: 提示数据，包含id, from_user_id, from_user_name, content, group_id等
    """
    logger.info(f"📤 [Peer Prompt推送] 开始向用户{user_id}推送Peer Prompt...")
    
    payload = json.dumps({
        "type": "peer_prompt_received",
        "data": {
            "prompt_id": prompt_data.get("id"),
            "from_user_id": prompt_data.get("from_user_id"),
            "from_user_name": prompt_data.get("from_user_name"),
            "content": prompt_data.get("content"),
            "group_id": prompt_data.get("group_id"),
            "created_at": prompt_data.get("created_at")
        }
    })
    
    _send_q.put((user_id, payload))
    logger.info(f"📤 [Peer Prompt推送] WebSocket推送成功: {prompt_data.get('from_user_name')} → {user_id}")


