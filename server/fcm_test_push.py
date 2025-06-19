import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# === 配置部分 ===
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
SERVICE_ACCOUNT_FILE = "firebase-key.json"  # ✅ 替换成你的实际路径
FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/collaborative-ai-chatbot/messages:send"
DEVICE_TOKEN = "fbgSliOyQ_-Rp31Prdfkb6:APA91bHwV-_TbgDX-ZlWbEFGmcKoxoYesR-q-sGl0pdIsvCBMxmOIA3oh2ergjVJ6saQLk8JRL6qO8Ns38szDmWjzVzxNjAKessTW-qsjCrJYYAOHaPjhEM"

# === 获取 access token ===
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
credentials.refresh(Request())
access_token = credentials.token

# === 构造消息 ===
payload = {
    "message": {
        "token": DEVICE_TOKEN,
        "notification": {
            "title": "📦 测试推送",
            "body": "这是一条来自 Python 的 Firebase v1 API 测试通知"
        },
        "data": {
            "type": "test",
            "summary": "onMessageReceived 是否工作？",
            "suggestion": "请检查 Android 端日志"
        }
    }
}

# === 发送请求 ===
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json; UTF-8",
}

response = requests.post(
    FCM_ENDPOINT,
    headers=headers,
    data=json.dumps(payload)
)

print("🔧 FCM 响应状态码:", response.status_code)
print("📬 响应内容:", response.json())