

import requests

# 云端 FastAPI 接口地址（替换为你实际后端的接口）
API_URL = "http://localhost:8000/api/voice_result"

def upload_result(speaker: str, text: str, timestamp: str = None):
    """
    将识别结果上传到服务器。
    参数：
    - speaker: 说话人名称
    - text: 识别到的文本内容
    - timestamp: 可选的时间戳（字符串）
    """
    payload = {
        "speaker": speaker,
        "text": text,
        "timestamp": timestamp,
    }
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        print(f"✅ 已上传：{speaker}: {text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 上传失败：{e}")