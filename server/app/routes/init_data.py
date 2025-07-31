import traceback
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi import Body

from server.app.database import db
from server.app.logger.logger_loader import logger

router = APIRouter()

CHAT_AGENDAS = [
    {
        "agenda_title": "任务议题：「搞点抽象的」— 年轻人的情绪表达新姿势",
        "agenda_description": "「搞抽象」已经成为部分大学生表达个性、传递情绪的方式。从「整活文学」到「精神小伙图腾」，这些看似离谱的内容，实则承载着青年人对现实、关系与自我身份的幽默回应和情绪出口。\n\n请分析「搞抽象」背后的心理动机，理解Z世代如何在表达与保护之间寻找平衡，以及如何通过这种独特方式缓解压力。最后，请设想一个智能工具来支持「搞抽象」文化，讨论它如何理解用户情绪状态、帮助用户创造有趣的抽象内容，并体现对这种表达方式的理解。",
        "output_requirements": {
            "findings": {
                "example": [
                    {
                        "point": "发现1：年轻人更倾向在数字平台上表达自我情绪",
                        "support": "支持依据：某研究指出，短视频平台评论区成为情绪宣泄窗口（《数字原住民研究》2021）"
                    },
                    {
                        "point": "发现2：他们对效率工具有高度依赖，但也表现出焦虑感",
                        "support": "数据支持：据某AI助手报告，80%用户使用工具同时伴随「完不成也焦虑」的情绪标签"
                    }
                ],
                "instructions": "请总结你们对该现象的理解，并识别Z世代背后的心理或行为特征。每一条发现必须结合真实案例、新闻报道、社交平台内容或学术研究等支持性资料，不接受无根据推测或仅表达个人观点。",
                "title": "关键发现或共识（分点列出，每点需配支持依据）"
            },
            "proposals": {
                "example": [
                    {
                        "point": "建议1：引入节奏调节功能，依据用户状态动态调整互动强度",
                        "support": "有研究指出自适应式节奏设计可降低用户的认知负荷（见《Adaptive Interaction Design》2022）"
                    },
                    {
                        "point": "建议2：增加记录与回顾机制，帮助用户更好复盘情绪或行为",
                        "support": "参考灵感：某健康类App允许用户回顾每日情绪轨迹，用户复购率提升约20%"
                    }
                ],
                "instructions": "请提出你们的构想方向、工具/产品的关键功能、使用场景或互动方式设想。每一点建议都需要有实际产品、相关研究或典型案例支持，说明它的合理性与潜在影响。",
                "title": "初步构想或解决建议（分点列出，每点需配支持依据）"
            }
        }
    },
    {
        "agenda_title": "任务议题：「今天约搭子了吗？」— 轻社交时代的关系新范式",
        "agenda_description": "「搭子文化」成为新兴社交趋势：年轻人偏好「饭搭子」「剧搭子」「运动搭子」，临时结伴、不求深交。它带来了低负担、边界清晰的社交形式，逐渐取代传统深度社交成为主流选择之一。\n\n请分析「搭子文化」背后的心理动机，理解Z世代如何在社交互动与个体自由之间寻找平衡，以及如何通过轻量关系缓解孤独感。最后，请设想一个智能匹配工具来支持「搭子文化」，讨论它如何理解用户需求、帮助用户找到合适的「搭子」，并体现对这种社交趋势的理解。",
        "output_requirements": {
            "findings": {
                "example": [
                    {
                        "point": "发现1：年轻人更倾向在数字平台上表达自我情绪",
                        "support": "支持依据：某研究指出，短视频平台评论区成为情绪宣泄窗口（《数字原住民研究》2021）"
                    },
                    {
                        "point": "发现2：他们对效率工具有高度依赖，但也表现出焦虑感",
                        "support": "数据支持：据某AI助手报告，80%用户使用工具同时伴随「完不成也焦虑」的情绪标签"
                    }
                ],
                "instructions": "请总结你们对该现象的理解，并识别Z世代背后的心理或行为特征。每一条发现必须结合真实案例、新闻报道、社交平台内容或学术研究等支持性资料，不接受无根据推测或仅表达个人观点。",
                "title": "关键发现或共识（分点列出，每点需配支持依据）"
            },
            "proposals": {
                "example": [
                    {
                        "point": "建议1：引入节奏调节功能，依据用户状态动态调整互动强度",
                        "support": "有研究指出自适应式节奏设计可降低用户的认知负荷（见《Adaptive Interaction Design》2022）"
                    },
                    {
                        "point": "建议2：增加记录与回顾机制，帮助用户更好复盘情绪或行为",
                        "support": "参考灵感：某健康类App允许用户回顾每日情绪轨迹，用户复购率提升约20%"
                    }
                ],
                "instructions": "请提出你们的构想方向、工具/产品的关键功能、使用场景或互动方式设想。每一点建议都需要有实际产品、相关研究或典型案例支持，说明它的合理性与潜在影响。",
                "title": "初步构想或解决建议（分点列出，每点需配支持依据）"
            }
        }
    }
]



@router.post("/api/init_data")
async def init_data(input_data: dict = Body(...)):
    """
    更新用户信息（包括 name, academic_background, academic_advantages）
    """
    try:
        global CHAT_AGENDAS
        init_data = input_data.get("init_data")
        for item in init_data:
            group_name = item.get("group_name")
            agenda_title = item.get("agenda_title")

            group_id = str(uuid.uuid4())
            db.collection("groups").document(group_id).set({
                "id": group_id,
                "name": group_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ai_bot_id": str(uuid.uuid4()),
                "is_active": "true",
                "group_goal": "",
                "control_group": item.get("control_group"),
                "note_id": str(uuid.uuid4()),
                "task_intro": agenda_title
            })

            session_id = str(uuid.uuid4())
            db.collection("chat_sessions").document(session_id).set({
                "id": session_id,
                "group_id": group_id,
                "session_title": f"{agenda_title} ({group_name})",
                "session_date": datetime.now(timezone.utc).isoformat(),
                "ai_memory": "{}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })

            for chat_agenda in CHAT_AGENDAS:
                if chat_agenda["agenda_title"] == agenda_title:
                    agenda_id = str(uuid.uuid4())
                    db.collection("chat_agendas").document(agenda_id).set({
                        "id": agenda_id,
                        "group_id": group_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "allocated_time_minutes": 30,
                        "session_id": session_id,
                        "status": "in_progress",
                        **chat_agenda
                    })

            users = item.get("users")
            for user in users:
                user_id = user.get("user_id")
                db.collection("users_info").document(user_id).set({
                    "user_id": user_id,
                    "name": user.get("name"),
                    "avatar_link": "https://i.pravatar.cc/150?img=1",
                    "academic_background": {
                        "major": "Computer Science",
                        "research_focus": "Artificial Intelligence and Machine Learning"
                    },
                    "academic_advantages": "Expert in AI algorithms, deep learning frameworks, and natural language processing.",
                    "device_token": user.get("device_token"),
                    "preferences": {},
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

                group_memberships_id = str(uuid.uuid4())
                db.collection("group_memberships").document(group_memberships_id).set({
                    "id": group_memberships_id,
                    "group_id": group_id,
                    "user_id": user_id,
                    "role": "member",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

        return {"message": "初始化数据成功"}
    except Exception as e:
        logger.error(f"❌ [初始化数据] 异常: {traceback.format_exc()}")

