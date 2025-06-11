from dotenv import load_dotenv
import os
load_dotenv()

APPID = os.getenv("TENCENT_APPID")
SECRET_ID = os.getenv("TENCENT_SECRET_ID")
SECRET_KEY = os.getenv("TENCENT_SECRET_KEY")

import websocket
import threading
import json
import time
import queue
import numpy as np

import hmac
import hashlib
import base64
import urllib.parse


# 腾讯云签名有效期（单位：秒）
EXPIRED_SECONDS = 3600  # 1小时有效期

def generate_ws_url(appid: str, secret_id: str, secret_key: str):
    endpoint = f"asr.cloud.tencent.com/asr/v2/{appid}"
    timestamp = int(time.time())
    expired = timestamp + EXPIRED_SECONDS
    nonce = 123456

    params_dict = {
        "appid": appid,
        "secretid": secret_id,
        "timestamp": timestamp,
        "expired": expired,
        "nonce": nonce
    }

    params = "&".join(f"{k}={params_dict[k]}" for k in sorted(params_dict))
    sign_str = f"GET{endpoint}?{params}"

    signature = hmac.new(
        secret_key.encode('utf-8'),
        sign_str.encode('utf-8'),
        hashlib.sha1
    ).digest()

    signature_base64 = base64.b64encode(signature).decode()
    signature_encoded = urllib.parse.quote(signature_base64)

    ws_url = f"wss://{endpoint}?{params}&signature={signature_encoded}"
    print("📦 签名字符串:", sign_str)
    print("🔗 WebSocket URL:", ws_url)
    return ws_url


# 腾讯云实时语音识别的 WebSocket URL（动态生成）
TENCENT_ASR_WS_URL = generate_ws_url(APPID, SECRET_ID, SECRET_KEY)

recognizer_streams = {}

class RecognizerStream:
    def __init__(self, speaker_name):
        self.speaker = speaker_name
        self.q = queue.Queue()
        self.ws = websocket.WebSocketApp(
            TENCENT_ASR_WS_URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.sender_thread = threading.Thread(target=self.send_loop, daemon=True)
        self.connected = False

    def start(self):
        self.thread.start()
        time.sleep(1)  # 等待连接建立
        self.sender_thread.start()

    def on_open(self, ws):
        print(f"🟢 [{self.speaker}] WebSocket 已连接")
        self.connected = True
        # 发送初始化配置消息
        init_payload = {
            "type": "start",
            "voice_id": f"{self.speaker}_{int(time.time())}",
            "data": {
                "appid": APPID,
                "format": "pcm",
                "rate": 16000,
                "channel": 1
            }
        }
        ws.send(json.dumps(init_payload))
        print(f"📤 [{self.speaker}] 初始化参数: {json.dumps(init_payload, indent=2)}")

    def on_message(self, ws, message):
        print(f"📨 [{self.speaker}] 收到消息: {message}")
        data = json.loads(message)
        if data.get("final"):
            result = data['result']['text']
            print(f"✅ [{self.speaker}] 识别结果: {result}")

    def on_error(self, ws, error):
        print(f"❌ [{self.speaker}] 错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔴 [{self.speaker}] WebSocket 已关闭 | 状态码: {close_status_code}, 原因: {close_msg}")
        self.connected = False

    def send_loop(self):
        while True:
            data = self.q.get()
            if self.connected:
                try:
                    print(f"📤 [{self.speaker}] 发送音频: {len(data.tobytes())} bytes")
                    self.ws.send(data.tobytes())
                except Exception as e:
                    print(f"⚠️ [{self.speaker}] 发送失败: {e}")
            time.sleep(0.1)

    def send_audio(self, audio_data: np.ndarray):
        self.q.put(audio_data)

def send_audio_stream(audio_data, speaker_name):
    """
    通过已有连接将音频发送给腾讯 ASR
    """
    if speaker_name not in recognizer_streams:
        recognizer_streams[speaker_name] = RecognizerStream(speaker_name)
        recognizer_streams[speaker_name].start()
    recognizer_streams[speaker_name].send_audio(audio_data)