import asyncio
from fastapi import APIRouter, HTTPException
from server.app.database import db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ========== 📌 小组管理 API ==========

# 获取所有小组信息
@router.get("/api/groups/")
async def get_groups():
    groups_ref = db.collection("groups")
    groups = [doc.to_dict() | {"id": doc.id} for doc in groups_ref.stream()]
    return groups

# 根据 group_id 获取小组详细信息
@router.get("/api/groups/{group_id}")
async def get_group(group_id: str):
    doc = db.collection("groups").document(group_id).get()
    if doc.exists:
        return doc.to_dict() | {"id": doc.id}
    else:
        raise HTTPException(status_code=404, detail="未找到该小组")

# 获取指定小组的成员列表
@router.get("/api/groups/{group_id}/members")
async def get_group_members(group_id: str):
    members_ref = db.collection("group_memberships").where("group_id", "==", group_id).stream()
    members = [doc.to_dict() | {"id": doc.id} for doc in members_ref]
    return members

class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    group_goal: Optional[str] = None
    control_group: Optional[str] = None

@router.post("/api/groups/{group_id}")
# 更新指定小组的信息（包括名称和目标）
async def update_group_info(group_id: str, update_data: GroupUpdateRequest):
    """
    更新小组的名称和目标
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")
    doc_ref = db.collection("groups").document(group_id)
    existing_doc = doc_ref.get()
    if not existing_doc.exists:
        raise HTTPException(status_code=404, detail="未找到该小组")

    doc_ref.update(update_fields)
    updated_data = existing_doc.to_dict() | update_fields | {"id": existing_doc.id}
    return {"message": "小组信息已更新", "data": updated_data}

@router.get("/api/user/{user_id}/group-context")
async def get_group_context_by_user(user_id: str):
    import time
    start_time = time.time()

    # 1. 查询 group_memberships，找到对应 group_id
    memberships = list(db.collection("group_memberships").where("user_id", "==", user_id).stream())
    if not memberships:
        raise HTTPException(status_code=404, detail="未找到该用户所在的小组")

    group_id = memberships[0].to_dict().get("group_id")

    # 2. 获取小组详情
    group_doc = db.collection("groups").document(group_id).get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="未找到小组详情")
    group_data = group_doc.to_dict() | {"id": group_doc.id}

    # 3. 获取组员列表
    member_docs = list(db.collection("group_memberships").where("group_id", "==", group_id).stream())
    member_ids = [doc.to_dict().get("user_id") for doc in member_docs]

    # 批量查询用户信息
    users_info_docs = list(db.collection("users_info").where("user_id", "in", member_ids).stream())
    users_infos = [doc.to_dict() for doc in users_info_docs]

    # 4. 获取最新 session
    session_docs = list(db.collection("chat_sessions")
        .where("group_id", "==", group_id)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream())
    session_data = session_docs[0].to_dict() | {"id": session_docs[0].id} if session_docs else None

    print(f"✅ get_group_context_by_user 用时: {round(time.time() - start_time, 3)}s")

    return {
        "group": group_data,
        "members": users_infos,
        "session": session_data
    }