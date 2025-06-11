import sounddevice as sd
import numpy as np

def record_audio_chunk(device_index: int, duration: float = 1.0, samplerate: int = 16000):
    """
    录制一段立体声音频，并返回左右声道的 numpy 数组。
    - 左声道 = channel 0 = 发言人 A
    - 右声道 = channel 1 = 发言人 B
    """
    frames = int(duration * samplerate)
    print(f"🎙️ 正在录制 {duration}s 的音频 ...")
    audio = sd.rec(frames, samplerate=samplerate, channels=2, dtype='int16', device=device_index)
    sd.wait()
    left_channel = audio[:, 0]
    right_channel = audio[:, 1]
    return left_channel, right_channel


# 持续录音与实时处理主循环
def continuous_recording(device_index: int, chunk_duration: float = 1.0, samplerate: int = 16000, callback=None):
    """
    持续录音，每次录制 chunk_duration 秒，并实时处理左右声道数据。
    可用于推送到语音识别 API。
    """
    print("🔄 开始持续录音，按 Ctrl+C 停止")
    try:
        while True:
            left_channel, right_channel = record_audio_chunk(
                device_index=device_index,
                duration=chunk_duration,
                samplerate=samplerate
            )
            if callback:
                callback(left_channel, right_channel)
            else:
                print(f"📤 发送 {chunk_duration}s 左声道音频（长度 {len(left_channel)}）")
                print(f"📤 发送 {chunk_duration}s 右声道音频（长度 {len(right_channel)}）")
            # 在这里调用语音识别 API，例如：
            # send_to_tencent_asr(user="Alice", audio_data=left_channel)
            # send_to_tencent_asr(user="Bob", audio_data=right_channel)
    except KeyboardInterrupt:
        print("\n🛑 已停止录音")


# 示例调用入口
if __name__ == "__main__":
    DEVICE_INDEX = 2  # 修改为你的麦克风设备索引

    def sample_callback(left, right):
        print("✅ 收到一段音频块")
        print("  🎧 左声道前10样本：", left[:10])
        print("  🎧 右声道前10样本：", right[:10])

    continuous_recording(device_index=DEVICE_INDEX, callback=sample_callback)
