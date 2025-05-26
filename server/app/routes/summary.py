from fastapi import APIRouter, HTTPException, Request
from google.cloud import firestore
from datetime import datetime
import uuid
from app.ai_provider import generate_response

router = APIRouter(prefix="/api/summary")
db = firestore.Client()

@router.post("/generate_summary/{group_id}")
async def trigger_ai_summary(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    group_id = body.get("group_id")
    summary_text = body.get("summary_text")
    ai_provider = body.get("ai_provider", "xai")
    if not summary_text:
        chat_docs = db.collection("chat_messages") \
            .where("group_id", "==", group_id) \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .limit(10).stream()
        chat_history = [doc.to_dict() for doc in chat_docs]
        conversation = "\n".join([msg["message"] for msg in chat_history])
        bot_id = body.get("chatbot_id")
        summary_text = generate_response(
            bot_id=bot_id,
            main_prompt=conversation,
            history_prompt="",
            prompt_type="real_time_summary",
            model="default",
            api_provider=ai_provider
        )
    if not group_id or not summary_text:
        raise HTTPException(status_code=400, detail="group_id and summary_text are required")

    doc_id = str(uuid.uuid4())
    doc_data = {
        "group_id": group_id,
        "content": summary_text,
        "type": "summary",
        "ai_provider": ai_provider,
        "created_at": datetime.utcnow(),
        "session_id": session_id,
    }
    db.collection("chat_summaries").document(doc_id).set(doc_data)
    return {"status": "ok", "id": doc_id}

@router.post("/generate_guidance/{group_id}")
async def trigger_ai_guidance(group_id: str, request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    group_id = group_id
    guidance_text = body.get("guidance_text")
    ai_provider = body.get("ai_provider", "xai")
    if not guidance_text:
        chat_docs = db.collection("chat_messages") \
            .where("group_id", "==", group_id) \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .limit(5).stream()
        chat_history = [doc.to_dict() for doc in chat_docs]
        conversation = "\n".join([msg["message"] for msg in chat_history])
        bot_id = body.get("chatbot_id")
        history_docs = db.collection("chat_summaries") \
            .where("group_id", "==", group_id) \
            .where("type", "==", "summary") \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .limit(1).stream()
        history_text = next((doc.to_dict()["content"] for doc in history_docs), "")
        guidance_text = generate_response(
            bot_id=bot_id,
            main_prompt=conversation,
            history_prompt=history_text,
            prompt_type="cognitive_guidance",
            model="default",
            api_provider=ai_provider
        )
    if not group_id or not guidance_text:
        raise HTTPException(status_code=400, detail="group_id and guidance_text are required")

    doc_id = str(uuid.uuid4())
    doc_data = {
        "group_id": group_id,
        "content": guidance_text,
        "type": "guidance",
        "ai_provider": ai_provider,
        "created_at": datetime.utcnow(),
        "session_id": session_id,
    }
    db.collection("chat_summaries").document(doc_id).set(doc_data)
    return {"status": "ok", "id": doc_id}

@router.get("/api/chat_summaries/{group_id}")
async def get_chat_summaries(group_id: str):
    query = db.collection("chat_summaries").where("group_id", "==", group_id).order_by("created_at")
    docs = query.stream()
    summaries = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return summaries