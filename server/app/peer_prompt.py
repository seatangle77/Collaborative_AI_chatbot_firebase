from firebase_admin import firestore
from server.app.database import db

# Peer Prompt 相关数据库操作
def insert_peer_prompt(data):
    """插入Peer Prompt记录"""
    doc_ref = db.collection("peer_prompts").document()
    data["id"] = doc_ref.id
    data["created_at"] = firestore.SERVER_TIMESTAMP
    data["push_sent"] = False
    doc_ref.set(data)
    return {"status": "inserted", "id": doc_ref.id}

def get_peer_prompts_by_user(user_id, group_id, page=1, page_size=10):
    """获取用户收到的Peer Prompts"""
    query = db.collection("peer_prompts").where("to_user_id", "==", user_id).where("group_id", "==", group_id)
    query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
    
    # 分页处理
    offset = (page - 1) * page_size
    docs = query.offset(offset).limit(page_size).stream()
    
    prompts = []
    for doc in docs:
        prompt_data = doc.to_dict()
        prompt_data["id"] = doc.id
        prompts.append(prompt_data)
    
    # 获取总数
    total_docs = query.stream()
    total = len(list(total_docs))
    
    return {
        "prompts": prompts,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def update_peer_prompt_push_status(prompt_id, push_sent=True, error_message=None):
    """更新Peer Prompt推送状态"""
    update_data = {
        "push_sent": push_sent,
        "push_sent_at": firestore.SERVER_TIMESTAMP
    }
    if error_message:
        update_data["push_error"] = error_message
    
    db.collection("peer_prompts").document(prompt_id).update(update_data)
    return {"status": "updated", "id": prompt_id}

def get_user_device_token(user_id):
    """获取用户设备token"""
    user_doc = db.collection("users_info").document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return user_data.get("device_token")
    return None

def get_user_name(user_id):
    """获取用户姓名"""
    user_doc = db.collection("users_info").document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return user_data.get("name", "未知用户")
    return "未知用户" 