import importlib.util
from jinja2 import Template
import os
import traceback
from app.database import db

# 获取组数据
def get_group_data(group_id):
    group = db.collection("groups").document(group_id).get().to_dict()
    agendas = [doc.to_dict() for doc in db.collection("chat_agendas").where("group_id", "==", group_id).order_by("created_at").stream()]
    member_ids = [doc.to_dict() for doc in db.collection("group_memberships").where("group_id", "==", group_id).stream()]
    user_ids = [m["user_id"] for m in member_ids]
    users = []
    if user_ids:
        # Firestore 'in' queries support up to 10 items, handle accordingly if needed
        users = [doc.to_dict() for doc in db.collection("users_info").where("user_id", "in", user_ids).stream()]

    user_data = [
        {
            "name": user["name"],
            "academic_background": f"{user['academic_background']['major']}，研究方向：{user['academic_background']['research_focus']}",
            "academic_advantages": user["academic_advantages"].strip()
        }
        for user in users
    ]

    return_data = {
        "group_name": group["name"],
        "group": {
            "goal": group["group_goal"].strip()
        },
        "agenda_title": agendas[0]["agenda_title"] if agendas else "",
        "agenda_description": agendas[0]["agenda_description"] if agendas else "",
        "users": user_data
    }
    if user_data:
        return_data["user"] = user_data[0]
    return return_data

def load_default_prompts(path="default_prompts.py"):
    full_path = os.path.join(os.path.dirname(__file__), path)
    spec = importlib.util.spec_from_file_location("default_prompts", full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEFAULT_PROMPTS

def generate_prompts_for_group(group_id: str):
    try:
        prompts = load_default_prompts("default_prompts.py")
        bot_query = db.collection("ai_bots").where("group_id", "==", group_id).limit(1).stream()
        bot_doc = next(bot_query, None)
        if not bot_doc:
            return
        bot = bot_doc.to_dict()
        bot_id = bot["id"]
        data = get_group_data(group_id)

        for prompt_name, content in prompts.items():
            try:
                template = Template(content["system_prompt"])
                filled_prompt = template.render(**data)
            except Exception as e:
                print(f"❌ 渲染失败 group_id={group_id}, prompt={prompt_name}: {e}")
                print("⚠️ 当前数据内容为：", data)
                continue
            field_name = f"{prompt_name}_systemprompt"
            
            versions_query = db.collection("ai_prompt_versions") \
                .where("ai_bot_id", "==", bot_id) \
                .where("prompt_type", "==", prompt_name) \
                .stream()
            existing_versions = [v.to_dict() for v in versions_query]
            version_numbers = [int(v["template_version"].lstrip("v")) for v in existing_versions if v["template_version"].startswith("v") and v["template_version"][1:].isdigit()]
            new_version = max(version_numbers, default=0) + 1
            template_version = f"v{new_version}"
            
            # Update ai_bots document
            bot_docs = db.collection("ai_bots").where("id", "==", bot_id).limit(1).stream()
            bot_doc_ref = next(bot_docs, None)
            if bot_doc_ref:
                bot_doc_ref.reference.update({field_name: filled_prompt})

            # Insert new version document
            db.collection("ai_prompt_versions").add({
                "ai_bot_id": bot_id,
                "group_id": group_id,
                "prompt_type": prompt_name,
                "rendered_prompt": filled_prompt,
                "template_version": template_version,
                "source": "auto",
                "is_active": False
            })
            print(f"✅ Updated {field_name} for bot {bot['name']}")
    except Exception as e:
        print("🔥 生成 prompts 失败（全局异常）:")
        traceback.print_exc()

def generate_prompts_for_personal_agent(agent_id: str):
    try:
        prompts = load_default_prompts("default_prompts.py")
        
        # 获取 agent 对应的 user_id
        user_query = db.collection("users_info").where("agent_id", "==", agent_id).limit(1).stream()
        user_doc = next(user_query, None)
        if not user_doc:
            raise ValueError(f"❌ 无法通过 agent_id={agent_id} 找到用户信息")
        user_info = user_doc.to_dict()
        user_id = user_info["user_id"]

        print(f"🧪 正在查询用户 user_id={user_id}")
        agent_query = db.collection("personal_agents").where("id", "==", agent_id).limit(1).stream()
        agent_doc = next(agent_query, None)
        if not agent_doc:
            print(f"❌ 未找到 agent 信息，agent_id={agent_id}")
            return
        agent_info = agent_doc.to_dict()

        membership_query = db.collection("group_memberships").where("user_id", "==", user_id).limit(1).stream()
        membership_doc = next(membership_query, None)
        group_goal = ""
        if membership_doc:
            membership = membership_doc.to_dict()
            group_id = membership.get("group_id")
            group_doc = db.collection("groups").document(group_id).get()
            if group_doc.exists:
                group_data = group_doc.to_dict()
                group_goal = group_data["group_goal"].strip()

        user_data = {
            "user": {
                "name": user_info["name"],
                "academic_background": f"{user_info['academic_background']['major']}，研究方向：{user_info['academic_background']['research_focus']}",
                "academic_advantages": user_info["academic_advantages"].strip()
            },
            "group_name": "",
            "group": {
                "goal": group_goal
            }
        }

        new_versions = []

        for prompt_name in ["term_explanation", "knowledge_followup"]:
            if prompt_name in prompts:
                try:
                    template = Template(prompts[prompt_name]["system_prompt"])
                    filled_prompt = template.render(**user_data)
                    field_name = f"{prompt_name}_prompt"

                    # Update personal_agents document
                    personal_agents_query = db.collection("personal_agents").where("user_id", "==", user_id).limit(1).stream()
                    personal_agent_doc = next(personal_agents_query, None)
                    if personal_agent_doc:
                        personal_agent_doc.reference.update({field_name: filled_prompt})

                    versions_query = db.collection("agent_prompt_versions") \
                        .where("agent_id", "==", agent_id) \
                        .where("prompt_type", "==", prompt_name) \
                        .stream()
                    existing_versions = [v.to_dict() for v in versions_query]
                    version_numbers = [int(v["template_version"].lstrip("v")) for v in existing_versions if v["template_version"].startswith("v") and v["template_version"][1:].isdigit()]
                    new_version = max(version_numbers, default=0) + 1
                    template_version = f"v{new_version}"

                    db.collection("agent_prompt_versions").add({
                        "agent_id": agent_id,
                        "prompt_type": prompt_name,
                        "rendered_prompt": filled_prompt,
                        "template_version": template_version,
                        "source": "auto",
                        "is_active": False
                    })

                    new_versions.append({
                        "agent_id": agent_id,
                        "prompt_type": prompt_name,
                        "version": template_version
                    })

                    print(f"✅ Rendered {field_name} for user {user_id}")
                except Exception as e:
                    print(f"❌ 渲染失败 user_id={user_id}, prompt={prompt_name}: {e}")
                    print("⚠️ 当前数据内容为：", user_data)

        return new_versions if new_versions else []

    except Exception as e:
        print("🔥 生成个人 agent prompts 失败：")
        traceback.print_exc()
        return None

def set_prompt_version_active(bot_id: str, prompt_type: str, version: str):
    """
    将指定 bot 的某类 prompt 的某个版本设置为当前激活状态
    """
    # 先将该 bot + prompt_type 的所有版本设为 inactive
    versions_query = db.collection("ai_prompt_versions") \
        .where("ai_bot_id", "==", bot_id) \
        .where("prompt_type", "==", prompt_type) \
        .stream()
    for doc in versions_query:
        doc.reference.update({"is_active": False})

    # 然后将目标版本设为 active
    active_query = db.collection("ai_prompt_versions") \
        .where("ai_bot_id", "==", bot_id) \
        .where("prompt_type", "==", prompt_type) \
        .where("template_version", "==", version) \
        .limit(1).stream()
    active_doc = next(active_query, None)
    if active_doc:
        active_doc.reference.update({"is_active": True})

def set_personal_prompt_version_active(agent_id: str, prompt_type: str, version: str):
    """
    将指定个人 agent 的某类 prompt 的某个版本设置为当前激活状态
    """
    # 先将该 agent + prompt_type 的所有版本设为 inactive
    versions_query = db.collection("agent_prompt_versions") \
        .where("agent_id", "==", agent_id) \
        .where("prompt_type", "==", prompt_type) \
        .stream()
    for doc in versions_query:
        doc.reference.update({"is_active": False})

    # 然后将目标版本设为 active
    active_query = db.collection("agent_prompt_versions") \
        .where("agent_id", "==", agent_id) \
        .where("prompt_type", "==", prompt_type) \
        .where("template_version", "==", version) \
        .limit(1).stream()
    active_doc = next(active_query, None)
    if active_doc:
        active_doc.reference.update({"is_active": True})

# 第三步：读取模板并替换
if __name__ == "__main__":
    bots_query = db.collection("ai_bots").stream()
    all_bots = [doc.to_dict() for doc in bots_query]
    for b in all_bots:
        generate_prompts_for_group(b["group_id"])