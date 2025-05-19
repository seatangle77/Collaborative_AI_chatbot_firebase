from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from app.database import supabase_client
from app.ai_provider import generate_response
import datetime
import uuid

router = APIRouter()

# ✅ 数据模型：创建 insight 所需字段
class DiscussionInsightCreate(BaseModel):
    group_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message_text: str  # 用户查询的文本
    ai_provider: Optional[str] = "xai"  # AI 提供商，默认为 xai
    agent_id: Optional[str] = None  # 个人 AI Agent ID
    model: Optional[str] = None  # 新增字段：模型名
    prompt_version: Optional[str] = None  # 新增字段：提示版本
    term_name: Optional[str] = None  # 新增字段：术语名称

# ✅ 数据模型：返回 insight 记录的结构
class DiscussionInsightResponse(BaseModel):
    id: int
    group_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    message_id: Optional[int]
    insight_text: str
    created_at: str
    term_name: Optional[str]
    insight_id: Optional[str]  # 新增字段

# ✅ 创建 AI 查询记录
@router.post("/api/discussion_insights", response_model=DiscussionInsightResponse)
async def create_discussion_insight(data: DiscussionInsightCreate):
    """
    使用 AI 生成跨学科术语解释，并将结果保存至 discussion_insights 表。
    """
    try:
        if not data.agent_id:
            raise HTTPException(status_code=400, detail="term_explanation 类型必须传入 agent_id")

        # 生成 AI 响应
        ai_response = generate_response(
            bot_id=data.agent_id,
            main_prompt=data.message_text,
            prompt_type="term_explanation",
            api_provider=data.ai_provider,
            agent_id=data.agent_id,
            model=data.ai_provider  # 新增参数
        )

        # 构建新记录
        new_insight = {
            "group_id": data.group_id,
            "session_id": data.session_id,
            "user_id": data.user_id,
            "message_id": None,
            "insight_text": ai_response,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "agent_id": data.agent_id,
            "prompt_version": data.prompt_version,  # 新增字段
            "model": data.model,  # 新增字段
            "term_name": data.message_text,  # 修改为 message_text
            "insight_id": str(uuid.uuid4()),  # 新增字段
        }

        # 插入数据库
        insert_response = supabase_client.from_("discussion_insights").insert(new_insight).execute()
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="插入数据库失败")

        return DiscussionInsightResponse(**insert_response.data[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ✅ 获取所有查询记录
@router.get("/api/discussion_insights", response_model=List[DiscussionInsightResponse])
async def get_all_discussion_insights():
    """
    获取 discussion_insights 表中所有记录。
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")


# ✅ 按 group_id 获取查询记录
@router.get("/api/discussion_insights/{group_id}", response_model=List[DiscussionInsightResponse])
async def get_discussion_insights_by_group(group_id: str):
    """
    获取特定 group 的 discussion_insights 查询记录。
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*").eq("group_id", group_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")


# ✅ 按 group_id 和 session_id 获取查询记录
@router.get("/api/discussion_insights/{group_id}/{session_id}", response_model=List[DiscussionInsightResponse])
async def get_discussion_insights_by_session(group_id: str, session_id: str):
    """
    获取特定 group 与 session 对应的 discussion_insights 查询记录。
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*") \
            .eq("group_id", group_id) \
            .eq("session_id", session_id) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")

# ✅ 按 group_id 和 agent_id 获取查询记录
@router.get("/api/discussion_insights/{group_id}/agent/{agent_id}", response_model=List[DiscussionInsightResponse])
async def get_discussion_insights_by_group_and_agent(group_id: str, agent_id: str):
    """
    获取特定 group 与 agent 对应的 discussion_insights 查询记录。
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*") \
            .eq("group_id", group_id) \
            .eq("agent_id", agent_id) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")
