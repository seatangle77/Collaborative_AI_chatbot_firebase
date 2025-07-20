import os
from dotenv import load_dotenv
import jpush
from jpush import common, JPush
import time

from server.app.database import db
from server.app.logger.logger_loader import logger

# 优先加载 .env.local（如果有），再加载 .env
load_dotenv('.env.local')
load_dotenv()

JPUSH_APP_KEY = os.getenv("JPUSH_APP_KEY", "你的AppKey")
JPUSH_MASTER_SECRET = os.getenv("JPUSH_MASTER_SECRET", "你的MasterSecret")

# 检查配置
if JPUSH_APP_KEY == "你的AppKey" or JPUSH_MASTER_SECRET == "你的MasterSecret":
    print("⚠️ 警告：JPush AppKey 或 MasterSecret 未正确配置")

print(f"[调试] JPUSH_APP_KEY={JPUSH_APP_KEY}, JPUSH_MASTER_SECRET={JPUSH_MASTER_SECRET}")

_jpush = JPush(JPUSH_APP_KEY, JPUSH_MASTER_SECRET)
_jpush.set_logging("WARNING")  # 改为WARNING级别，减少调试日志

def send_jpush_notification(alert, registration_id=None, extras=None):
    """
    发送JPush通知
    :param alert: 通知内容
    :param registration_id: 设备ID（单推），为None时为广播
    :param extras: 附加数据（字典）
    :return: 发送结果
    """
    start_time = time.time()
    print(f"📤 [JPush推送] 开始推送通知，设备ID: {registration_id}")
    
    try:
        push = _jpush.create_push()
        push.platform = jpush.all_
        if registration_id:
            push.audience = jpush.audience(jpush.registration_id(registration_id))
        else:
            push.audience = jpush.all_
        push.notification = jpush.notification(alert=alert)
        if extras:
            push.message = jpush.message(msg_content=alert, extras=extras)
        
        response = push.send()
        duration = time.time() - start_time
        print(f"✅ [JPush推送] 推送成功，耗时{duration:.2f}秒: {response}")
        return response
        
    except common.Unauthorized as e:
        duration = time.time() - start_time
        print(f"❌ [JPush推送] 鉴权失败，耗时{duration:.2f}秒，请检查AppKey和MasterSecret: {e}")
        return None
    except common.APIConnectionException as e:
        duration = time.time() - start_time
        print(f"❌ [JPush推送] 连接失败，耗时{duration:.2f}秒: {e}")
        return None
    except common.JPushFailure as e:
        duration = time.time() - start_time
        print(f"❌ [JPush推送] 推送失败，耗时{duration:.2f}秒: {e}")
        return None
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ [JPush推送] 未知异常，耗时{duration:.2f}秒: {e}")
        return None


async def jpush_personal_share_message(user_id: str, from_user: str, detail_type: str, detail_status: str,
                                      group_id: str):
    """向指定用户推送Share异常消息 - 同时推送到PC和移动设备"""
    start_time = time.time()
    logger.info(f"📤 [极光推送] 开始向用户{user_id}推送Share异常消息...")

    # 2. 极光推送到移动设备
    jpush_success = False
    try:

        # 获取用户的device_token
        user_doc = db.collection("users_info").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            device_token = user_data.get("device_token")

            if device_token:
                # 获取发送者姓名
                from_user_doc = db.collection("users_info").document(from_user).get()
                from_user_name = "未知用户"
                if from_user_doc.exists:
                    from_user_data = from_user_doc.to_dict()
                    from_user_name = from_user_data.get("name", "未知用户")

                # 构建推送内容
                alert = f"{from_user_name}分享了异常信息：{detail_type}"
                extras = {
                    "type": "share",
                    "from_user": from_user,
                    "from_user_name": from_user_name,
                    "detail_type": detail_type,
                    "detail_status": detail_status,
                    "group_id": group_id,
                    "title": "组员异常分享",
                    "body": alert
                }

                # 发送极光推送
                result = send_jpush_notification(
                    alert=alert,
                    registration_id=device_token,
                    extras=extras
                )

                if result:
                    jpush_success = True
                    logger.info(
                        f"📱 [Share推送] 极光推送成功，用户: {from_user_name} → {user_data.get('name', '未知用户')}")
                else:
                    logger.info(f"❌ [Share推送] 极光推送失败")
            else:
                logger.info(f"⚠️ [Share推送] 用户{user_id}没有device_token")
        else:
            logger.info(f"⚠️ [Share推送] 用户{user_id}信息不存在")

    except Exception as e:
        logger.info(f"❌ [Share推送] 极光推送异常: {e}")

    # 3. 记录推送结果
    duration = time.time() - start_time
    if jpush_success:
        logger.info(f"✅ [Share推送] 用户{user_id}推送完成，耗时{duration:.2f}秒")
        logger.info(f"   - 极光推送: {'✅' if jpush_success else '❌'}")
    else:
        logger.info(f"❌ [Share推送] 用户{user_id}推送失败，耗时{duration:.2f}秒")
        logger.info(f"   - 极光推送: ❌")