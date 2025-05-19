from fastapi import APIRouter, HTTPException
from app.database import supabase_client
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ========== 📌 小组管理 API ==========

# 获取所有小组信息
@router.get("/api/groups/")
async def get_groups():
    return supabase_client.table("groups").select("*").execute().data

# 根据 group_id 获取小组详细信息
@router.get("/api/groups/{group_id}")
async def get_group(group_id: str):
    return supabase_client.table("groups").select("*").eq("id", group_id).execute().data

# 获取指定小组的成员列表
@router.get("/api/groups/{group_id}/members")
async def get_group_members(group_id: str):
    return supabase_client.table("group_memberships").select("*").eq("group_id", group_id).execute().data

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

    response = (
        supabase_client.table("groups")
        .update(update_fields)
        .eq("id", group_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="未找到该小组或更新失败")

    return {"message": "小组信息已更新", "data": response.data[0]}
