from fastapi import APIRouter, HTTPException, Query, Body
from google.cloud import firestore
from app.generate_prompts import (
    generate_prompts_for_personal_agent,
    set_personal_prompt_version_active,
)
import traceback
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import db

router = APIRouter()


# 🎯 为某个用户的 AI Agent 生成 prompts（并激活最新版本）
@router.post("/api/personal_agents/generate_prompt/{agent_id}")
async def generate_prompt_for_personal_agent(agent_id: str):
    """
    为个人 AI Agent 生成 prompts（包含 term_explanation 和 knowledge_followup）
    并将生成的版本设为当前激活版本
    """
    try:
        new_versions = generate_prompts_for_personal_agent(agent_id)
        for item in new_versions:
            set_personal_prompt_version_active(item["agent_id"], item["prompt_type"], item["version"])
        return {
            "message": f"{agent_id} 的 prompts 已生成并激活",
            "data": new_versions,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 📚 获取某个 AI Agent 的所有 prompt 历史版本（term_explanation 和 knowledge_followup）
@router.get("/api/personal_prompt_versions/{agent_id}")
async def get_personal_prompt_versions(agent_id: str):
    """
    获取指定个人 AI Agent 的 prompt 历史版本（term_explanation 和 knowledge_followup）
    """
    try:
        result = {}
        for prompt_type in ["term_explanation", "knowledge_followup"]:
            print(f"🔥 查询 agent_id={agent_id}, prompt_type={prompt_type}")
            versions_ref = db.collection("agent_prompt_versions")
            try:
                snapshots = (
                    versions_ref.where("agent_id", "==", agent_id)
                                .where("prompt_type", "==", prompt_type)
                                .order_by("created_at", direction=firestore.Query.DESCENDING)
                                .stream()
                )
                print("✅ 查询成功，开始迭代")
                query_result = []
                for doc in snapshots:
                    item = doc.to_dict()
                    item["is_current"] = item.get("is_active", False)
                    query_result.append(item)
                result[prompt_type] = query_result
                print(f"✅ 返回 {len(query_result)} 条")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本失败: {str(e)}")

        
# 📌 根据 agent_id 获取个人 AI Agent 的信息
@router.get("/api/personal_agents/{agent_id}")
async def get_personal_agent(agent_id: str):
    """
    获取指定 ID 的个人 AI Agent 信息
    """
    try:
        doc = db.collection("personal_agents").document(agent_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="未找到该 Agent")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Agent 信息失败: {str(e)}")

# 🔄 更新个人 AI Agent 的模型字段
@router.put("/api/personal_agents/{agent_id}/model")
async def update_personal_agent_model(agent_id: str, model: str = Body(..., embed=True)):
    """
    更新个人 AI Agent 的模型字段（model）
    """
    try:
        agent_ref = db.collection("personal_agents").document(agent_id)
        agent_ref.update({"model": model})
        updated_doc = agent_ref.get()
        return {"message": "模型已更新", "data": updated_doc.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# 获取 agent 反馈
@router.get("/api/ai_agents/feedback")
async def get_ai_agent_feedback(
    agent_id: str = Query(...),
    target_id: Optional[str] = Query(None),
    prompt_type: Optional[str] = Query(None)
):
    """
    获取某 Agent 对指定目标的反馈记录（用于前端初始化点赞/点踩/评论状态）
    """
    if not prompt_type:
        return {"message": "No prompt_type specified", "data": None}
    try:
        feedback_ref = db.collection("ai_agent_feedback")
        query = feedback_ref.where("agent_id", "==", agent_id).where("prompt_type", "==", prompt_type)
        if target_id:
            query = query.where("target_id", "==", target_id)
        results = list(query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream())
        if not results:
            return {"message": "No feedback found", "data": None}
        return results[0].to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈失败: {str(e)}")

# 提交 agent 反馈
class AIAgentFeedbackRequest(BaseModel):
    agent_id: str
    target_id: str
    ai_model: Optional[str]
    prompt_type: str
    prompt_version: Optional[str]
    like: Optional[bool] = None
    dislike: Optional[bool] = None
    comment_text: Optional[str]

@router.post("/api/ai_agents/feedback")
async def submit_ai_agent_feedback(data: AIAgentFeedbackRequest):
    """
    提交 AI Agent 反馈。以 (agent_id, target_id, prompt_type) 为唯一标识。
    """
    try:
        if not data.target_id:
            raise HTTPException(status_code=400, detail="target_id 不能为空")

        if not data.prompt_type:
            raise HTTPException(status_code=400, detail="prompt_type 不能为空")

        feedback_ref = db.collection("ai_agent_feedback")
        query = feedback_ref.where("agent_id", "==", data.agent_id)\
                            .where("target_id", "==", data.target_id)\
                            .where("prompt_type", "==", data.prompt_type)
        existing = list(query.stream())

        feedback_payload = {
            "agent_id": data.agent_id,
            "target_id": data.target_id,
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
            doc_id = existing[0].id
            feedback_ref.document(doc_id).update(feedback_payload)
            updated_doc = feedback_ref.document(doc_id).get()
            return {"message": "反馈已更新", "data": updated_doc.to_dict()}
        else:
            doc_ref = feedback_ref.document()
            doc_ref.set(feedback_payload)
            return {"message": "反馈已提交", "data": feedback_payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈处理失败: {str(e)}")
