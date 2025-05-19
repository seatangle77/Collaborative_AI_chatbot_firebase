from fastapi import APIRouter, HTTPException, Query
from app.database import supabase_client
from app.generate_prompts import (
    generate_prompts_for_group,
    set_prompt_version_active,
)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

router = APIRouter()

@router.get("/api/ai_bots")
async def get_all_ai_bots():
    """
    获取所有 AI Bots（供前端显示所有 bot）
    """
    try:
        result = supabase_client.table("ai_bots").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取所有 bots 失败: {str(e)}")

# ========== 📌 AI 机器人管理 API ==========

@router.get("/api/ai_bots/feedback")
async def get_ai_bot_feedback(
    user_id: str = Query(...),
    bot_id: str = Query(...),
    target_id: Optional[str] = Query(None),
    prompt_type: Optional[str] = Query(None)
):
    """
    获取某用户对指定目标的反馈记录（用于前端初始化点赞/点踩/评论状态）

    参数：
        - user_id: 用户 ID
        - bot_id: AI Bot ID
        - target_id: 被评价目标 ID（如 chat_summary 的 ID）
        - prompt_type: 被评价目标类型（如 'chat_summary'）

    返回：
        - feedback_type: 'like'、'dislike' 或 'comment'
        - comment_text（可选）
        - prompt_type（可选）
        - prompt_version（可选）
    """
    if not prompt_type:
        return {"message": "No prompt_type specified", "data": None}
    try:
        query = (
            supabase_client.table("ai_bot_feedback")
            .select("*")
            .eq("user_id", user_id)
            .eq("bot_id", bot_id)
            .eq("prompt_type", prompt_type)
        )
        if target_id:
            query = query.eq("target_id", target_id)
        result = query.order("created_at", desc=True).limit(1).execute()
        if not result.data:
            return {"message": "No feedback found", "data": None}
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈失败: {str(e)}")

@router.get("/api/ai_bots/{bot_id}")
async def get_ai_bot(bot_id: str):
    """
    根据 AI 机器人 ID 获取具体的机器人信息
    """
    return supabase_client.table("ai_bots").select("*").eq("id", bot_id).execute().data

@router.get("/api/ai_bots/group/{group_id}")
async def get_ai_bots_by_group(group_id: str):
    """
    获取特定小组的 AI 机器人
    """
    return supabase_client.table("ai_bots").select("*").eq("group_id", group_id).execute().data

@router.get("/api/ai_bots/user/{user_id}")
async def get_ai_bots_by_user(user_id: str):
    """
    获取属于特定用户的 AI 机器人
    """
    return supabase_client.table("ai_bots").select("*").eq("user_id", user_id).execute().data

# 🎯 为某个小组的 AI Bot 生成 prompts（并激活最新版本）
@router.post("/api/ai_bots/generate_prompt/{group_id}")
async def generate_prompt_for_group(group_id: str):
    """
    为指定小组的 AI Bot 生成 prompts（包含 real_time_summary、cognitive_guidance、summary_to_knowledge）
    并将生成的版本设为当前激活版本
    """
    try:
        new_versions = generate_prompts_for_group(group_id)
        for item in new_versions:
            set_prompt_version_active(item["bot_id"], item["prompt_type"], item["version"])
        return {"message": f"{group_id} 的 prompts 已生成并激活", "data": new_versions}
    except Exception as e:
        #traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 📚 获取某个 AI Bot 的特定类型 prompt 的所有历史版本
@router.get("/api/ai_prompt_versions/{bot_id}/{prompt_type}")
async def get_prompt_versions(bot_id: str, prompt_type: str, version: str = Query(None)):
    """
    获取指定 AI Bot 的 prompt 历史版本（可筛选 prompt_type 和 version）
    """
    try:
        query = (
            supabase_client.table("ai_prompt_versions")
            .select("*")
            .eq("ai_bot_id", bot_id)
            .eq("prompt_type", prompt_type)
        )
        if version:
            query = query.eq("template_version", version)

        result = query.order("created_at", desc=True).execute()
        for item in result.data:
            item["is_current"] = item.get("is_active", False)
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本失败: {str(e)}")

# ========== ✅ 更新和获取 AI Bot 的 model 字段 ==========

class BotModelUpdateRequest(BaseModel):
    model: str

@router.put("/api/ai_bots/{bot_id}/model")
async def update_ai_bot_model(bot_id: str, update_data: BotModelUpdateRequest):
    """
    根据 AI Bot 的 ID 更新其 model 字段
    """
    try:
        update_response = (
            supabase_client.table("ai_bots")
            .update({"model": update_data.model})
            .eq("id", bot_id)
            .execute()
        )
        if not update_response.data:
            raise HTTPException(status_code=404, detail="未找到指定的 AI Bot 或更新失败")
        return {"message": "model 字段已更新", "data": update_response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.get("/api/ai_bots/{bot_id}/model")
async def get_ai_bot_model(bot_id: str):
    """
    根据 AI Bot 的 ID 获取其 model 字段
    """
    try:
        result = (
            supabase_client.table("ai_bots")
            .select("model")
            .eq("id", bot_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="未找到指定的 AI Bot")
        return {"model": result.data[0].get("model", None)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

class AIBotFeedbackRequest(BaseModel):
    user_id: str
    bot_id: str
    target_id: Optional[str] = None
    like: Optional[bool] = None
    dislike: Optional[bool] = None
    comment_text: Optional[str] = None
    ai_model: str
    prompt_type: Optional[str] = None
    prompt_version: Optional[str] = None

@router.post("/api/ai_bots/feedback")
async def submit_ai_bot_feedback(data: AIBotFeedbackRequest):
    """
    提交 AI Bot 反馈。以 (user_id, bot_id, target_id, prompt_type) 为唯一标识，判断是否存在反馈。
    """
    try:
        if not data.target_id:
            raise HTTPException(status_code=400, detail="target_id 不能为空")

        if not data.prompt_type:
            raise HTTPException(status_code=400, detail="prompt_type 不能为空")

        target_id = data.target_id

        if data.prompt_type == "real_time_summary" or data.prompt_type == "cognitive_guidance":
            target_id = data.target_id
        else:
            raise HTTPException(status_code=400, detail="target_id 缺失或不合法")

        # 查询是否已有相同 prompt_type 的反馈（user_id, bot_id, target_id, prompt_type）
        existing = (
            supabase_client.table("ai_bot_feedback")
            .select("*")
            .eq("user_id", data.user_id)
            .eq("bot_id", data.bot_id)
            .eq("target_id", target_id)
            .eq("prompt_type", data.prompt_type)
            .execute()
            .data
        )

        # 正常反馈流程
        feedback_payload = {
            "user_id": data.user_id,
            "bot_id": data.bot_id,
            "target_id": target_id,
            "ai_model": data.ai_model,
            "prompt_type": data.prompt_type,
            "prompt_version": data.prompt_version,
            "created_at": datetime.utcnow().isoformat()
        }

        if data.like is not None:
            feedback_payload["like"] = data.like
        if data.dislike is not None:
            feedback_payload["dislike"] = data.dislike
        if data.comment_text is not None:
            feedback_payload["comment_text"] = data.comment_text

        if existing:
            update_response = (
                supabase_client.table("ai_bot_feedback")
                .update(feedback_payload)
                .eq("id", existing[0]["id"])
                .execute()
            )
            return {"message": "反馈已更新", "data": update_response.data[0]}
        else:
            insert_response = (
                supabase_client.table("ai_bot_feedback")
                .insert(feedback_payload)
                .execute()
            )
            return {"message": "反馈已提交", "data": insert_response.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈处理失败: {str(e)}")