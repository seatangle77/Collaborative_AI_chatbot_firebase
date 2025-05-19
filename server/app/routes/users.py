from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import supabase_client

router = APIRouter()

# ✅ 获取所有用户信息
@router.get("/api/users/")
async def get_users():
    return supabase_client.table("users_info").select("*").execute().data

# ✅ 获取指定用户信息
@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    return supabase_client.table("users_info").select("*").eq("user_id", user_id).execute().data

# ✅ 获取用户的 AI 代理信息
@router.get("/api/users/{user_id}/agent")
async def get_user_agent(user_id: str):
    """
    获取用户的 AI 代理信息 (agent_id, agent_name)
    """
    result = (
        supabase_client.table("users_info")
        .select("agent_id, personal_agents(name)")
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="未找到该用户的 AI 代理")

    agent_info = result.data[0]
    return {
        "agent_id": agent_info.get("agent_id"),
        "agent_name": agent_info.get("personal_agents", {}).get("name", "无 AI 代理"),
    }

# ✅ 用户信息更新模型
class UserInfoUpdateRequest(BaseModel):
    name: Optional[str] = None
    academic_background: Optional[dict] = None  # JSON 字段
    academic_advantages: Optional[str] = None

# ✅ 更新用户信息
@router.put("/api/users/{user_id}")
async def update_user_info(user_id: str, update_data: UserInfoUpdateRequest):
    """
    更新用户信息（包括 name, academic_background, academic_advantages）
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    response = (
        supabase_client.table("users_info")
        .update(update_fields)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="未找到该用户或更新失败")

    return {"message": "用户信息已更新", "data": response.data[0]}
