from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.database import supabase_client
from app.websocket_routes import push_chat_message, push_ai_summary

router = APIRouter()

# ========== 📌 获取聊天历史记录 ==========
@router.get("/api/chat/{group_id}")
async def get_chat_history(group_id: str):
    """
    获取指定小组的聊天历史记录（按时间倒序排列）
    """
    return (
        supabase_client.table("chat_messages")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

# ✅ 定义发送消息的数据结构
class ChatMessage(BaseModel):
    group_id: str
    user_id: Optional[str] = None
    chatbot_id: Optional[str] = None
    message: str
    role: str = Field(default="user")
    message_type: str = Field(default="text")
    sender_type: str = Field(default="user")
    speaking_duration: Optional[int] = 0
    session_id: Optional[str] = None

# ========== 📌 发送聊天消息 ==========
@router.post("/api/chat/send")
async def send_chat_message(payload: ChatMessage):
    """
    发送聊天消息，同时存入数据库并通过 WebSocket 推送
    """
    data = payload.dict()

    # ✅ 插入数据库
    inserted_data = supabase_client.table("chat_messages").insert(data).execute().data

    if inserted_data:
        await push_chat_message(payload.group_id, inserted_data[0])  # ✅ WebSocket 推送消息

    return inserted_data

# ========== 📌 获取当前小组的活跃聊天会话 ==========
@router.get("/api/sessions/{group_id}")
async def get_current_session(group_id: str):
    """
    获取指定小组的当前活跃 Session（聊天会话）

    参数:
        - group_id (str): 小组 ID

    返回:
        - 该小组最新的 session 信息（如果有）
    """
    sessions = (
        supabase_client.table("chat_sessions")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if not sessions:
        raise HTTPException(status_code=404, detail="未找到该小组的活跃 session")

    return sessions[0]

# ========== 📌 获取指定 session 的聊天议程 ==========
@router.get("/api/chat/agenda/session/{session_id}")
async def get_agenda_by_session(session_id: str):
    """
    获取指定 session 关联的所有议程项（chat_agendas）

    参数:
        - session_id (str): 聊天 session 的 ID

    返回:
        - 该 session 下的议程列表（按创建时间升序）
    """
    agendas = (
        supabase_client.table("chat_agendas")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
    )

    if not agendas:
        raise HTTPException(status_code=404, detail="未找到该 session 相关的议程")

    return agendas

# ✅ 定义议程创建数据结构
class AgendaCreateRequest(BaseModel):
    group_id: str
    session_id: str
    agenda_title: str
    agenda_description: Optional[str] = ""
    status: Optional[str] = "not_started"

# ========== 📌 创建新的聊天议程项 ==========
@router.post("/api/chat/agenda")
async def create_agenda(data: AgendaCreateRequest):
    """
    新增一个议程项（chat agenda）

    参数:
        - group_id: 所属小组
        - session_id: 关联的聊天 session
        - agenda_title: 议程标题
        - agenda_description: 描述（可选）
        - status: 状态（默认 not_started）

    返回:
        - 创建成功的议程项信息
    """
    try:
        insert_data = {
            "group_id": data.group_id,
            "session_id": data.session_id,
            "agenda_title": data.agenda_title,
            "agenda_description": data.agenda_description,
            "status": data.status,
        }

        response = supabase_client.table("chat_agendas").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="新增议程失败")

        return {"message": "议程已创建", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建议程失败: {str(e)}")

# ✅ 定义议程更新结构
class AgendaUpdateRequest(BaseModel):
    agenda_title: Optional[str] = None
    agenda_description: Optional[str] = None
    status: Optional[str] = None

# ========== 📌 更新指定议程项 ==========
@router.put("/api/chat/agenda/{agenda_id}")
async def update_agenda(agenda_id: str, update_data: AgendaUpdateRequest):
    """
    修改指定议程项的标题、描述或状态

    参数:
        - agenda_id: 议程项 ID
        - update_data: 更新字段（部分可选）

    返回:
        - 更新后的议程项数据
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    update_response = (
        supabase_client.table("chat_agendas")
        .update(update_fields)
        .eq("id", agenda_id)
        .execute()
    )

    if not update_response.data:
        raise HTTPException(status_code=404, detail="未找到要更新的议程")

    latest = (
        supabase_client.table("chat_agendas")
        .select("*")
        .eq("id", agenda_id)
        .execute()
        .data[0]
    )

    return {"message": "议程已更新", "data": latest}

# ========== 📌 删除指定议程项 ==========
@router.delete("/api/chat/agenda/{agenda_id}")
async def delete_agenda(agenda_id: str):
    """
    删除指定的议程项

    参数:
        - agenda_id: 议程项 ID

    返回:
        - 删除成功的议程项信息
    """
    try:
        response = (
            supabase_client.table("chat_agendas")
            .delete()
            .eq("id", agenda_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="未找到要删除的议程")
        return {"message": "议程已删除", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除议程失败: {str(e)}")

# ========== 📌 获取小组的 AI 聊天总结记录 ==========
@router.get("/api/chat_summaries/{group_id}")
async def get_chat_summaries(group_id: str):
    """
    获取指定小组的 AI 聊天总结（按时间倒序）
    """
    return (
        supabase_client.table("chat_summaries")
        .select("*")
        .eq("group_id", group_id)
        .order("summary_time", desc=True)
        .execute()
        .data
    )

# ========== 📌 手动触发一次 AI 聊天总结 ==========
@router.post("/api/chat_summaries/{group_id}")
async def trigger_ai_summary(group_id: str):
    """
    手动触发一次 AI 聊天总结
    """
    await push_ai_summary(group_id)
    return {"message": "AI 会议总结已触发"}

# ========== 📌 获取指定 session 的 AI 聊天总结 ==========
@router.get("/api/chat_summaries/session/{session_id}")
async def get_chat_summaries_by_session(session_id: str):
    """
    获取指定 session 的 AI 聊天总结（按时间倒序）
    """
    summaries = (
        supabase_client.table("chat_summaries")
        .select("*")
        .eq("session_id", session_id)
        .order("summary_time", desc=True)
        .execute()
        .data
    )

    if not summaries:
        return JSONResponse(
            content=[], 
            status_code=200, 
            headers={"Access-Control-Allow-Origin": "*"}
        )

    return JSONResponse(
        content=summaries, 
        status_code=200, 
        headers={"Access-Control-Allow-Origin": "*"}
    )
