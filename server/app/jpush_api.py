import os
from dotenv import load_dotenv
import jpush
from jpush import common, JPush
import time

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