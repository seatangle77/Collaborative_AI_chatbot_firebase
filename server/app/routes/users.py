from fastapi import Body
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import db

router = APIRouter()

# ✅ 获取所有用户信息
@router.get("/api/users/")
async def get_users():
    users_ref = db.collection("users_info")
    docs = users_ref.stream()
    return [doc.to_dict() for doc in docs]

# ✅ 获取指定用户信息
@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    doc_ref = db.collection("users_info").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="未找到该用户信息")
    return doc.to_dict()

# ✅ 用户信息更新模型
class UserInfoUpdateRequest(BaseModel):
    name: Optional[str] = None
    academic_background: Optional[dict] = None  # JSON 字段
    academic_advantages: Optional[str] = None
    device_token: Optional[str] = None

# ✅ 更新用户信息
@router.put("/api/users/{user_id}")
async def update_user_info(user_id: str, update_data: UserInfoUpdateRequest):
    """
    更新用户信息（包括 name, academic_background, academic_advantages）
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    doc_ref = db.collection("users_info").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="未找到该用户或更新失败")

    doc_ref.update(update_fields)
    updated_doc = doc_ref.get()

    return {"message": "用户信息已更新", "data": updated_doc.to_dict()}


# 仅更新用户 device_token 字段
@router.put("/api/users/{user_id}/device_token")
async def update_user_device_token(user_id: str, token_data: dict = Body(...)):
    """
    仅更新用户的 device_token 字段
    """
    device_token = token_data.get("device_token")
    if not device_token:
        raise HTTPException(status_code=400, detail="未提供 device_token")

    doc_ref = db.collection("users_info").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="未找到该用户")

    doc_ref.update({"device_token": device_token})
    return {"message": "device_token 已更新", "device_token": device_token}