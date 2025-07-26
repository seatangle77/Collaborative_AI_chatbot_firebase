import os
from dotenv import load_dotenv
import jpush
from jpush import common, JPush
import time

from server.app.database import db
from server.app.peer_prompt import get_user_device_token, get_user_name
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
        device_token = get_user_device_token(user_id)

        if device_token:
            # 获取发送者姓名
            from_user_name = get_user_name(from_user)

            # 构建推送内容
            alert = f"组员提醒：分享了异常信息：{detail_type}"
            extras = {
                "type": "share",
                "from_user": from_user,
                "from_user_name": from_user_name,
                "detail_type": detail_type,
                "detail_status": detail_status,
                "group_id": group_id,
                "title": "组员提醒",
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

def send_jpush_peer_prompt(to_user_id: str, from_user_name: str, content: str, prompt_data: dict):
    """
    发送Peer Prompt极光推送
    :param to_user_id: 接收者用户ID
    :param from_user_name: 发送者姓名
    :param content: 提示内容
    :param prompt_data: 提示数据
    :return: 推送结果
    """
    start_time = time.time()
    logger.info(f"📤 [Peer Prompt推送] 开始向用户{to_user_id}推送Peer Prompt...")

    try:
        # 获取用户的device_token
        device_token = get_user_device_token(to_user_id)

        if not device_token:
            logger.info(f"⚠️ [Peer Prompt推送] 用户{to_user_id}没有device_token")
            return False

        # 构建推送内容
        alert = f"组员提醒：{content}"
        extras = {
            "type": "peer_prompt",
            "prompt_id": prompt_data.get("id"),
            "from_user_id": prompt_data.get("from_user_id"),
            "from_user_name": from_user_name,
            "group_id": prompt_data.get("group_id"),
            "content": content,
            "title": "组员提醒",
            "body": alert
        }

        # 发送极光推送
        result = send_jpush_notification(
            alert=alert,
            registration_id=device_token,
            extras=extras
        )

        if result:
            user_name = get_user_name(to_user_id)
            logger.info(f"📱 [Peer Prompt推送] 极光推送成功，用户: {from_user_name} → {user_name}")
            return True
        else:
            logger.info(f"❌ [Peer Prompt推送] 极光推送失败")
            return False

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ [Peer Prompt推送] 推送异常，耗时{duration:.2f}秒: {e}")
        return False

def format_jpush_peer_prompt_message(title: str, content: str, extras: dict):
    """
    格式化Peer Prompt极光推送消息
    :param title: 推送标题
    :param content: 推送内容
    :param extras: 附加数据
    :return: 推送消息对象
    """
    try:
        push = _jpush.create_push()
        push.platform = jpush.all_
        
        # 设置推送内容
        push.notification = jpush.notification(
            alert=content,
            android={
                "title": title,
                "content": content,
                "extras": extras,
                "priority": 2,  # 高优先级
                "style": 1,     # 大文本样式
                "alert_type": 1 # 提示音
            },
            ios={
                "alert": {
                    "title": title,
                    "body": content
                },
                "extras": extras,
                "sound": "default",
                "badge": "+1"
            }
        )
        
        # 设置消息内容
        push.message = jpush.message(
            msg_content=content,
            extras=extras
        )
        
        # 设置选项
        push.options = {
            "time_to_live": 86400,  # 24小时过期
            "apns_production": True  # 生产环境
        }
        
        return push
        
    except Exception as e:
        logger.error(f"❌ [Peer Prompt推送] 格式化消息失败: {e}")
        return None