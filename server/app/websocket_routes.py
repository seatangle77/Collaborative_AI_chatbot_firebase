from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import db as firestore_client
from app.ai_provider import generate_response  # ✅ 统一管理 AI API 提供商
import json
import asyncio
from datetime import datetime, timedelta
import uuid
from google.cloud import firestore
import os

def get_bot_id_by_group(group_id: str) -> str:
    bots_ref = firestore_client.collection("ai_bots").where("group_id", "==", group_id).limit(1).stream()
    for bot in bots_ref:
        return bot.to_dict().get("id")
    return None

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

            # ✅ 处理前端触发 AI 认知引导请求
            if received_data.get("type") == "trigger_ai_guidance":
                ai_provider = received_data.get("aiProvider", "xai")
                print(f"🚀 触发 AI 认知引导: group_id={group_id}, 使用 API: {ai_provider}")
                await check_cognitive_guidance(group_id, ai_provider)
                continue

            # ✅ 处理常规聊天消息
            await push_chat_message(group_id, received_data)

            print(f"📩 WebSocket 收到消息: {data} (group {group_id})")

    except WebSocketDisconnect:
        connected_clients[group_id].remove(websocket)
        if len(connected_clients[group_id]) == 0:
            del connected_clients[group_id]


# ✅ **推送聊天消息**
async def push_chat_message(group_id, message):
    """仅推送 WebSocket，不存入数据库"""

    if not message or "message" not in message or not message["message"].strip():
        print(f"⚠️ 跳过空消息: {message}")
        return
    
        # ✅ **检测是否 AI 生成的消息**
    is_ai_message = message.get("message_type") == "ai_guidance"

    chat_message_entry = {
        "msgId": str(uuid.uuid4()),
        "group_id": group_id,
        "user_id": message.get("user_id"),
        "message": message.get("message"),
        "role": message.get("role", "bot" if is_ai_message else "user"),  # ✅ AI 设为 assistant
        "created_at": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
        "message_type": message.get("message_type"),
        "sender_type": "bot" if is_ai_message else message.get("sender_type", "user"),  # ✅ AI 设为 bot
        "chatbot_id": message.get("chatbot_id"),
        "speaking_duration": len(message.get("message", "")) * 80 ,  # ✅ AI 语音时长计算
        "session_id": message.get("session_id")
    }

    # ✅ **仅推送 WebSocket，不再存数据库**
    if group_id in connected_clients:
        message_payload = json.dumps({"type": "message", "message": chat_message_entry})
        for client in connected_clients[group_id]:
            await client.send_text(message_payload)

    print(f"📤 聊天消息已通过 WebSocket 发送: {chat_message_entry}")

# ✅ **检测是否需要 AI 认知参与引导**
async def check_cognitive_guidance(group_id: str, api_provider: str):
    """基于最近的 5 条消息，判断是否需要 AI 介入，并生成引导信息"""
    # 🔍 检查是否已存在 ai_guidance 消息，避免重复生成
    existing_guidance = firestore_client.collection("chat_messages") \
        .where("group_id", "==", group_id) \
        .where("message_type", "==", "ai_guidance") \
        .order_by("created_at", direction=firestore.Query.DESCENDING) \
        .limit(1) \
        .stream()

    for doc in existing_guidance:
        last_time = doc.to_dict().get("created_at")
        if last_time:
            print("⚠️ 已存在 ai_guidance，跳过本次生成")
            return

    chat_history = []
    chat_docs = firestore_client.collection("chat_messages").where("group_id", "==", group_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(5).stream()
    for doc in chat_docs:
        chat_history.append(doc.to_dict())

    if not chat_history:
        return

    conversation = "\n".join([msg["message"] for msg in chat_history])
    conversation_content = f"以下是团队最近的聊天记录，请基于此内容分析讨论质量，并提供合适的知识拓展和引导建议：\n\n{conversation}"

    bot_id = get_bot_id_by_group(group_id)

    print(f"🪐 生成 AI bot 聊天干预: group_id={group_id}，使用 API: {api_provider}，传入main prompt: {conversation_content}")

    guidance_response = generate_response(
        bot_id=bot_id,
        main_prompt=conversation_content,  # 主要内容（最近聊天）
        prompt_type="cognitive_guidance",
        model="default",
        api_provider=api_provider
    )

    print(f"🤖 AI bot 聊天干预生成成功: {guidance_response}")


    if not guidance_response or guidance_response.strip() == "":
        print("✅ AI 评估: 无需介入")
        return

    try:
        guidance_response_clean = guidance_response.strip().strip("```json").strip("```")
        guidance_data = json.loads(guidance_response_clean)
        needs_intervention = guidance_data["guidance"]["needs_intervention"]
        suggestion = guidance_data["guidance"]["suggestion"]
    except Exception as e:
        print(f"❌ AI 认知引导 JSON 解析失败: {e}")
        return

    if not needs_intervention:
        print("✅ AI 评估: 无需介入")
        return
    

# ✅ 通过 group_id 获取 AI 机器人 ID 和 user_id
    bot_data = []
    bot_docs = firestore_client.collection("ai_bots").where("group_id", "==", group_id).limit(1).stream()
    for doc in bot_docs:
        bot_data.append(doc.to_dict())

    if bot_data:
        chatbot_id = bot_data[0]["id"]
        user_id = bot_data[0]["user_id"]  # ✅ AI 机器人对应的 user_id
    else:
        chatbot_id = None
        user_id = None

    # ✅ 通过 group_id 获取当前活跃的 session_id
    session_data = []
    session_docs = firestore_client.collection("chat_sessions").where("group_id", "==", group_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
    for doc in session_docs:
        session_data.append(doc.to_dict())
    session_id = session_data[0]["id"] if session_data else None

    ai_message = {
        "group_id": group_id,
        "user_id": user_id,
        "message": suggestion,
        "role": "bot",
        "message_type": "ai_guidance",
        "sender_type": "bot",
        "chatbot_id": chatbot_id,
        "session_id": session_id
    }

    # ✅ 入库 AI 认知引导消息
    firestore_client.collection("chat_messages").add(ai_message)

    await push_chat_message(group_id, ai_message)