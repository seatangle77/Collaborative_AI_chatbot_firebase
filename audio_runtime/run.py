import threading
import time
import numpy as np
import sounddevice as sd
from recognizer import send_audio_stream
from speaker_config import SPEAKER_MAPPING

DEVICE_INDEX = None  # 设置为 RODE RX 的音频输入设备索引
SAMPLERATE = 16000
BLOCKSIZE = 1024  # 每次读取的帧数（~64ms）

buffers = {
    0: bytearray(),  # 左声道缓存
    1: bytearray(),  # 右声道缓存
}

def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"⚠️ 音频状态异常: {status}")
    left = indata[:, 0].tobytes()
    right = indata[:, 1].tobytes()
    buffers[0].extend(left)
    buffers[1].extend(right)

def stream_sender(channel_index, speaker_name):
    while True:
        if len(buffers[channel_index]) >= 3200:  # ≈100ms音频 (16kHz × 0.1s × 2 bytes)
            chunk = buffers[channel_index][:3200]
            buffers[channel_index] = buffers[channel_index][3200:]
            send_audio_stream(np.frombuffer(chunk, dtype=np.int16), speaker_name)
        else:
            time.sleep(0.05)

if __name__ == "__main__":
    print("🚀 正在启动持续流式语音识别 ...")

    stream = sd.InputStream(
        samplerate=SAMPLERATE,
        channels=2,
        blocksize=BLOCKSIZE,
        dtype='int16',
        device=DEVICE_INDEX,
        callback=audio_callback
    )
    stream.start()

    threads = []
    for channel_index, speaker in SPEAKER_MAPPING.items():
        t = threading.Thread(target=stream_sender, args=(channel_index, speaker), daemon=True)
        t.start()
        threads.append(t)

    while True:
        time.sleep(1)