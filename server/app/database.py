import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.local"))

# 环境区分加载 firebase_key_dict
ENV = os.getenv("ENV", "development")

if ENV == "production":
    firebase_key_str = os.getenv("FIREBASE_KEY_JSON")
    if firebase_key_str is None:
        raise RuntimeError("FIREBASE_KEY_JSON not set for production mode")
    firebase_key_dict = json.loads(firebase_key_str)
else:
    firebase_key_str = os.getenv("FIREBASE_KEY_JSON")
    if firebase_key_str is None:
        raise RuntimeError("FIREBASE_KEY_JSON not set in .env.local for development mode")
    firebase_key_dict = json.loads(firebase_key_str)
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

def get_engagement_feedback_by_user(user_id):
    return [doc.to_dict() for doc in db.collection("engagement_feedback").where("user_id", "==", user_id).stream()]

def insert_engagement_feedback(data):
    doc_ref = db.collection("engagement_feedback").document(data["id"])
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
