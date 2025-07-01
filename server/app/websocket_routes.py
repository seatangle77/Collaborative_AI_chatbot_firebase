from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

websocket_router = APIRouter()

# 存储 WebSocket 连接
connected_clients = {}

@websocket_router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    """WebSocket 连接管理"""
    await websocket.accept()
    
    if group_id not in connected_clients:
        connected_clients[group_id] = []

    connected_clients[group_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 收到 WebSocket 数据: {data}")  # ✅ 添加日志，查看原始数据

            received_data = json.loads(data)

            print(f"📩 WebSocket 收到消息: {data} (group {group_id})")

    except WebSocketDisconnect:
        connected_clients[group_id].remove(websocket)
        if len(connected_clients[group_id]) == 0:
            del connected_clients[group_id]

async def push_agenda_stage(group_id: str, stage: int):
    """向当前小组所有客户端推送议程阶段变更"""
    if group_id in connected_clients:
        payload = json.dumps({
            "type": "agenda_stage_update",
            "stage": stage
        })
        for client in connected_clients[group_id]:
            await client.send_text(payload)

    print(f"📤 已向 group {group_id} 推送议程阶段: {stage}")

async def push_personal_share_message(user_id: str, from_user: str, detail_type: str, detail_status: str, group_id: str):
    """向指定用户推送Share异常消息"""
    if user_id in connected_clients:
        payload = json.dumps({
            "type": "share",
            "from_user": from_user,
            "detail_type": detail_type,
            "detail_status": detail_status,
            "group_id": group_id
        })
        for client in connected_clients[user_id]:
            await client.send_text(payload)
        print(f"📤 已向 user {user_id} 推送Share异常: {detail_type}, {detail_status}")