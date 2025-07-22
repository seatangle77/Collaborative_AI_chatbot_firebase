import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# 优先加载 .env.local（如果有），再加载 .env
load_dotenv('.env.local')
load_dotenv()

# 环境区分加载 firebase_key_dict
ENV = os.getenv("ENV", "development")

if ENV == "production":
    firebase_key_str = os.getenv("FIREBASE_KEY_JSON")
    if firebase_key_str is None:
        raise RuntimeError("FIREBASE_KEY_JSON not set for production mode")
    firebase_key_dict = json.loads(firebase_key_str)
else:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # 获取当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_dir = os.path.dirname(current_file_path)
    # 获取当前目录的上一级目录
    parent_dir = os.path.dirname(current_dir)
    cred_path = os.path.join(parent_dir, cred_path)

    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        firebase_key_str = os.getenv("FIREBASE_KEY_JSON")
        if firebase_key_str is None:
            raise RuntimeError("FIREBASE_KEY_JSON not set in .env.local for development mode")
        firebase_key_dict = json.loads(firebase_key_str)
        cred = credentials.Certificate(firebase_key_dict)
    # if using path, firebase_key_dict is not needed; if using dict, cred is already set
    # 'cred' is set in both branches above
if ENV == "production":
    cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore 封装数据库操作方法

def get_discussion_core_by_group(group_id):
    return [doc.to_dict() for doc in db.collection("discussion_core").where("group_id", "==", group_id).stream()]

def insert_discussion_core(data):
    doc_ref = db.collection("discussion_core").document(data["id"])
    doc_ref.set(data)
    return {"status": "inserted", "id": doc_ref.id}

def get_chat_messages_by_group(group_id):
    return [doc.to_dict() for doc in db.collection("chat_messages").where("group_id", "==", group_id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()]

def insert_chat_message(data):
    doc_ref = db.collection("chat_messages").document(data["id"])
    doc_ref.set(data)
    return {"status": "inserted", "id": doc_ref.id}

def update_chat_agenda(agenda_id, update_fields: dict):
    db.collection("chat_agendas").document(agenda_id).update(update_fields)
    return {"status": "updated", "id": agenda_id}
