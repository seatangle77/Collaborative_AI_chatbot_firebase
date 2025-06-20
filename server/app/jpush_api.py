import os
import jpush
from jpush import common, JPush

JPUSH_APP_KEY = os.getenv("JPUSH_APP_KEY", "你的AppKey")
JPUSH_MASTER_SECRET = os.getenv("JPUSH_MASTER_SECRET", "你的MasterSecret")

_jpush = JPush(JPUSH_APP_KEY, JPUSH_MASTER_SECRET)
_jpush.set_logging("DEBUG")

def send_jpush_notification(alert, registration_id=None, extras=None):
    """
    发送JPush通知
    :param alert: 通知内容
    :param registration_id: 设备ID（单推），为None时为广播
    :param extras: 附加数据（字典）
    :return: 发送结果
    """
    push = _jpush.create_push()
    push.platform = jpush.all_
    if registration_id:
        push.audience = jpush.audience(jpush.registration_id(registration_id))
    else:
        push.audience = jpush.all_
    push.notification = jpush.notification(alert=alert, android=extras, ios=extras)
    try:
        response = push.send()
        print(f"✅ JPush 推送成功: {response}")
        return response
    except common.Unauthorized:
        print("❌ JPush 鉴权失败，请检查AppKey和MasterSecret")
    except common.APIConnectionException:
        print("❌ JPush 连接失败")
    except common.JPushFailure as e:
        print(f"❌ JPush 推送失败: {e}")
    except Exception as e:
        print(f"❌ JPush 未知异常: {e}")
    return None 