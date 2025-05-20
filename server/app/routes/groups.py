from fastapi import APIRouter, HTTPException
from app.database import db
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

@router.put("/api/groups/{group_id}")
# 更新指定小组的信息（包括名称和目标）
async def update_group_info(group_id: str, update_data: GroupUpdateRequest):
    """
    更新小组的名称和目标
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")
    doc_ref = db.collection("groups").document(group_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="未找到该小组")

    doc_ref.update(update_fields)
    updated_doc = doc_ref.get()
    return {"message": "小组信息已更新", "data": updated_doc.to_dict() | {"id": updated_doc.id}}
