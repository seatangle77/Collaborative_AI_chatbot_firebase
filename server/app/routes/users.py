from fastapi import Body
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from server.app.database import db
from firebase_admin import messaging
from dotenv import load_dotenv
from server.app.jpush_api import send_jpush_notification

load_dotenv()

router = APIRouter()

# ✅ 获取所有用户信息
@router.get("/api/users/")
async def get_users():
    users_ref = db.collection("users_info")
    docs = users_ref.stream()
    users = [doc.to_dict() for doc in docs]

    print("🟢 [get_users] API 已被触发")
    # 移除推送逻辑，只返回用户列表
    return users

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
    
    # 更新成功后发送极光推送通知
    try:
        send_jpush_notification(
            alert="✅ 设备令牌更新成功：您的设备已成功注册推送服务。",
            registration_id=device_token,
            extras={
                "type": "device_token_update",
                "title": "✅ 设备令牌更新成功",
                "body": "您的设备已成功注册推送服务。",
                "user_id": user_id,
                "status": "success"
            }
        )
        print(f"✅ 设备令牌更新成功，已推送通知至: {device_token}")
    except Exception as e:
        print(f"⚠️ 推送通知失败: {e}")
    
    return {"message": "device_token 已更新", "device_token": device_token}

# Peer Prompt 相关模型和接口
class PeerPromptRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    group_id: str
    content: str

# 发送Peer Prompt
@router.post("/api/users/peer-prompt/send")
async def send_peer_prompt(request: PeerPromptRequest):
    """
    发送Peer Prompt
    """
    try:
        # 验证用户是否在同一小组
        from_user_doc = db.collection("users_info").document(request.from_user_id).get()
        to_user_doc = db.collection("users_info").document(request.to_user_id).get()
        
        if not from_user_doc.exists or not to_user_doc.exists:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 防止用户给自己发送提示
        if request.from_user_id == request.to_user_id:
            raise HTTPException(status_code=400, detail="不能给自己发送提示")
        
        # 验证内容长度
        if len(request.content) > 100:
            raise HTTPException(status_code=400, detail="提示内容不能超过100个字符")
        
        # 保存到数据库
        from server.app.peer_prompt import insert_peer_prompt, get_user_name, update_peer_prompt_push_status
        from server.app.jpush_api import send_jpush_peer_prompt
        from server.app.websocket_routes import push_peer_prompt_received
        
        prompt_data = {
            "from_user_id": request.from_user_id,
            "to_user_id": request.to_user_id,
            "group_id": request.group_id,
            "content": request.content
        }
        
        result = insert_peer_prompt(prompt_data)
        if result["status"] != "inserted":
            raise HTTPException(status_code=500, detail="保存提示失败")
        
        prompt_id = result["id"]
        
        # 获取发送者姓名
        from_user_name = get_user_name(request.from_user_id)
        
        # 发送极光推送
        push_success = send_jpush_peer_prompt(
            to_user_id=request.to_user_id,
            from_user_name=from_user_name,
            content=request.content,
            prompt_data={"id": prompt_id, **prompt_data}
        )
        
        # 更新推送状态
        update_peer_prompt_push_status(prompt_id, push_success)
        
        # 发送WebSocket推送
        await push_peer_prompt_received(
            user_id=request.to_user_id,
            prompt_data={
                "id": prompt_id,
                "from_user_id": request.from_user_id,
                "from_user_name": from_user_name,
                "content": request.content,
                "group_id": request.group_id
            }
        )
        
        return {
            "success": True,
            "message": "Peer prompt sent successfully",
            "data": {
                "prompt_id": prompt_id,
                "push_sent": push_success
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Peer Prompt发送] 异常: {e}")
        raise HTTPException(status_code=500, detail="发送失败")

# 获取收到的Peer Prompts
@router.get("/api/users/peer-prompt/received")
async def get_received_prompts(user_id: str, group_id: str, page: int = 1, page_size: int = 10):
    """
    获取用户收到的Peer Prompts
    """
    try:
        from server.app.peer_prompt import get_peer_prompts_by_user, get_user_name
        
        result = get_peer_prompts_by_user(user_id, group_id, page, page_size)
        
        # 为每个prompt添加发送者姓名
        for prompt in result["prompts"]:
            prompt["from_user_name"] = get_user_name(prompt["from_user_id"])
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"❌ [Peer Prompt获取] 异常: {e}")
        raise HTTPException(status_code=500, detail="获取失败")