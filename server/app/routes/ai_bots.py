from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from server.app.database import db
from typing import Optional
import uuid

router = APIRouter()

@router.get("/api/ai_bots")
async def get_all_ai_bots():
    """
    获取所有 AI Bots（供前端显示所有 bot）
    """
    try:
        docs = db.collection("ai_bots").stream()
        return [doc.to_dict() | {"id": doc.id} for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取所有 bots 失败: {str(e)}")

# ========== 📌 AI 机器人管理 API ==========

@router.get("/api/ai_bots/{bot_id}")
async def get_ai_bot(bot_id: str):
    """
    根据 AI 机器人 ID 获取具体的机器人信息
    """
    docs = db.collection("ai_bots").where("id", "==", bot_id).stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

@router.get("/api/ai_bots/group/{group_id}")
async def get_ai_bots_by_group(group_id: str):
    """
    获取特定小组的 AI 机器人
    """
    docs = db.collection("ai_bots").where("group_id", "==", group_id).stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

@router.get("/api/ai_bots/user/{user_id}")
async def get_ai_bots_by_user(user_id: str):
    """
    获取属于特定用户的 AI 机器人
    """
    docs = db.collection("ai_bots").where("user_id", "==", user_id).stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]


# ========== ✅ 更新和获取 AI Bot 的 model 字段 ==========

class BotModelUpdateRequest(BaseModel):
    model: str

@router.put("/api/ai_bots/{bot_id}/model")
async def update_ai_bot_model(bot_id: str, update_data: BotModelUpdateRequest):
    """
    根据 AI Bot 的 ID 更新其 model 字段
    """
    try:
        db.collection("ai_bots").document(bot_id).update({"model": update_data.model})
        doc = db.collection("ai_bots").document(bot_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="未找到指定的 AI Bot 或更新失败")
        return {"message": "model 字段已更新", "data": doc.to_dict() | {"id": doc.id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.get("/api/ai_bots/{bot_id}/model")
async def get_ai_bot_model(bot_id: str):
    """
    根据 AI Bot 的 ID 获取其 model 字段
    """
    try:
        doc = db.collection("ai_bots").document(bot_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="未找到指定的 AI Bot")
        return {"model": doc.to_dict().get("model", None)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")