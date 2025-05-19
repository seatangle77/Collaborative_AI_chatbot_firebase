import os
import supabase
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# 封装数据库操作方法

def get_discussion_core_by_group(group_id):
    return supabase_client.table("discussion_core").select("*").eq("group_id", group_id).execute()

def insert_discussion_core(data):
    return supabase_client.table("discussion_core").insert(data).execute()

def get_engagement_feedback_by_user(user_id):
    return supabase_client.table("engagement_feedback").select("*").eq("user_id", user_id).execute()

def insert_engagement_feedback(data):
    return supabase_client.table("engagement_feedback").insert(data).execute()

def get_chat_messages_by_group(group_id):
    return supabase_client.table("chat_messages").select("*").eq("group_id", group_id).order("created_at", desc=True).execute()

def insert_chat_message(data):
    return supabase_client.table("chat_messages").insert(data).execute()

def update_chat_agenda(agenda_id, update_fields: dict):
    return supabase_client.table("chat_agendas").update(update_fields).eq("id", agenda_id).execute()

# 可以根据需求添加更多表的封装方法
