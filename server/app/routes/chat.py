from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.database import db as firestore_db

router = APIRouter()

# ========== 📌 获取聊天历史记录 ==========
@router.get("/api/chat/{group_id}")
async def get_chat_history(group_id: str):
    """
    获取指定小组的聊天历史记录（按时间倒序排列）
    """
    docs = firestore_db.collection("chat_messages").where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING").stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

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
    msgid: Optional[str] = None

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
    try:
        print(f"🔍 查询 group_id: {group_id}")
        sessions = firestore_db.collection("chat_sessions") \
            .where("group_id", "==", group_id) \
            .order_by("created_at", direction="DESCENDING") \
            .limit(1).stream()
        sessions = list(sessions)
        if not sessions:
            raise HTTPException(status_code=404, detail="未找到该小组的活跃 session")
        return sessions[0].to_dict() | {"id": sessions[0].id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取 session 失败: {str(e)}")

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
    agendas = firestore_db.collection("chat_agendas").where("session_id", "==", session_id).order_by("created_at").stream()
    agendas = [doc.to_dict() | {"id": doc.id} for doc in agendas]
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

        doc_ref = firestore_db.collection("chat_agendas").add(insert_data)
        return {"message": "议程已创建", "data": insert_data | {"id": doc_ref[1].id}}
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
    doc_ref = firestore_db.collection("chat_agendas").document(agenda_id)
    doc_ref.update(update_fields)
    latest = doc_ref.get()
    return {"message": "议程已更新", "data": latest.to_dict() | {"id": agenda_id}}

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
        doc_ref = firestore_db.collection("chat_agendas").document(agenda_id)
        deleted = doc_ref.get()
        if not deleted.exists:
            raise HTTPException(status_code=404, detail="未找到要删除的议程")
        doc_ref.delete()
        return {"message": "议程已删除", "data": deleted.to_dict() | {"id": agenda_id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除议程失败: {str(e)}")


# ========== 📌 批量更新议程状态 ==========
@router.patch("/api/chat/agenda/reset_status/{group_id}")
async def reset_agenda_status(group_id: str, stage: int = Query(...)):
    """
    根据阶段重设小组的议程状态
    参数：
      - group_id: 小组 ID
      - stage: 当前阶段（0 表示全部未开始，1 表示第一个进行中，2 表示第二个进行中等）
    """
    try:
        print(f"🚀 reset_agenda_status called with group_id={group_id}, stage={stage}")

        agendas_ref = firestore_db.collection("chat_agendas").where("group_id", "==", group_id).order_by("created_at")
        agendas = list(agendas_ref.stream())

        print(f"📋 Retrieved {len(agendas)} agendas")

        if not agendas:
            raise HTTPException(status_code=404, detail="未找到该小组的议程")

        if stage == 5:
            for doc in agendas:
                doc_ref = firestore_db.collection("chat_agendas").document(doc.id)
                doc_ref.update({"status": "completed"})
            from app.websocket_routes import push_agenda_stage
            await push_agenda_stage(group_id, stage)
            return {"message": "所有议程状态已更新为 completed"}
        else:
            for idx, doc in enumerate(agendas):
                doc_ref = firestore_db.collection("chat_agendas").document(doc.id)
                if stage == 0:
                    new_status = "not_started"
                elif idx < stage - 1:
                    new_status = "completed"
                elif idx == stage - 1:
                    new_status = "in_progress"
                else:
                    new_status = "not_started"

                print(f"🔧 Updating agenda {doc.id}: index={idx}, new_status={new_status}")
                doc_ref.update({"status": new_status})

            from app.websocket_routes import push_agenda_stage
            await push_agenda_stage(group_id, stage)

        return {"message": f"议程状态已更新至阶段 {stage}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"更新议程状态失败: {str(e)}")
