import importlib.util
from jinja2 import Template
from supabase import create_client, Client
import os
import traceback

# 数据库连接
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 获取组数据
def get_group_data(group_id):
    group = supabase.table("groups").select("*").eq("id", group_id).single().execute().data
    agendas = supabase.table("chat_agendas").select("*").eq("group_id", group_id).order("created_at").execute().data
    member_ids = supabase.table("group_memberships").select("user_id").eq("group_id", group_id).execute().data
    user_ids = [m["user_id"] for m in member_ids]
    users = supabase.table("users_info").select("*").in_("user_id", user_ids).execute().data

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
        bot = supabase.table("ai_bots").select("*").eq("group_id", group_id).single().execute().data
        if not bot:
            return
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
            
            existing_versions = supabase.table("ai_prompt_versions").select("template_version").eq("ai_bot_id", bot_id).eq("prompt_type", prompt_name).execute().data
            version_numbers = [int(v["template_version"].lstrip("v")) for v in existing_versions if v["template_version"].startswith("v") and v["template_version"][1:].isdigit()]
            new_version = max(version_numbers, default=0) + 1
            template_version = f"v{new_version}"
            
            supabase.table("ai_bots").update({field_name: filled_prompt}).eq("id", bot_id).execute()
            supabase.table("ai_prompt_versions").insert({
                "ai_bot_id": bot_id,
                "group_id": group_id,
                "prompt_type": prompt_name,
                "rendered_prompt": filled_prompt,
                "template_version": template_version,
                "source": "auto"
            }).execute()
            print(f"✅ Updated {field_name} for bot {bot['name']}")
    except Exception as e:
        print("🔥 生成 prompts 失败（全局异常）:")
        traceback.print_exc()

def generate_prompts_for_personal_agent(agent_id: str):
    try:
        prompts = load_default_prompts("default_prompts.py")
        
        # 获取 agent 对应的 user_id
        user_result = supabase.table("users_info").select("*").eq("agent_id", agent_id).single().execute()
        if not user_result.data:
            raise ValueError(f"❌ 无法通过 agent_id={agent_id} 找到用户信息")
        user_info = user_result.data
        user_id = user_info["user_id"]

        print(f"🧪 正在查询用户 user_id={user_id}")
        agent_info = supabase.table("personal_agents").select("*").eq("id", agent_id).single().execute().data

        if not agent_info:
            print(f"❌ 未找到 agent 信息，agent_id={agent_id}")
            return

        agent_id = agent_info["id"]

        membership = supabase.table("group_memberships").select("group_id").eq("user_id", user_id).execute().data
        group_goal = ""
        if membership:
            group_id = membership[0]["group_id"]
            group_data = supabase.table("groups").select("group_goal").eq("id", group_id).single().execute().data
            if group_data:
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
                    supabase.table("personal_agents").update({field_name: filled_prompt}).eq("user_id", user_id).execute()

                    existing_versions = supabase.table("agent_prompt_versions").select("template_version").eq("agent_id", agent_id).eq("prompt_type", prompt_name).execute().data
                    version_numbers = [int(v["template_version"].lstrip("v")) for v in existing_versions if v["template_version"].startswith("v") and v["template_version"][1:].isdigit()]
                    new_version = max(version_numbers, default=0) + 1
                    template_version = f"v{new_version}"

                    supabase.table("agent_prompt_versions").insert({
                        "agent_id": agent_id,
                        "prompt_type": prompt_name,
                        "rendered_prompt": filled_prompt,
                        "template_version": template_version,
                        "source": "auto"
                    }).execute()

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
    supabase.table("ai_prompt_versions") \
        .update({"is_active": False}) \
        .eq("ai_bot_id", bot_id) \
        .eq("prompt_type", prompt_type) \
        .execute()

    # 然后将目标版本设为 active
    supabase.table("ai_prompt_versions") \
        .update({"is_active": True}) \
        .eq("ai_bot_id", bot_id) \
        .eq("prompt_type", prompt_type) \
        .eq("template_version", version) \
        .execute()

def set_personal_prompt_version_active(agent_id: str, prompt_type: str, version: str):
    """
    将指定个人 agent 的某类 prompt 的某个版本设置为当前激活状态
    """
    # 先将该 agent + prompt_type 的所有版本设为 inactive
    supabase.table("agent_prompt_versions") \
        .update({"is_active": False}) \
        .eq("agent_id", agent_id) \
        .eq("prompt_type", prompt_type) \
        .execute()

    # 然后将目标版本设为 active
    supabase.table("agent_prompt_versions") \
        .update({"is_active": True}) \
        .eq("agent_id", agent_id) \
        .eq("prompt_type", prompt_type) \
        .eq("template_version", version) \
        .execute()

# 第三步：读取模板并替换
if __name__ == "__main__":
    all_bots = supabase.table("ai_bots").select("group_id").execute().data
    for b in all_bots:
        generate_prompts_for_group(b["group_id"])