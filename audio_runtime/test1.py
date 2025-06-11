import threading

import pyaudio

import wave
import argparse


# audio = pyaudio.PyAudio()
# device_count = audio.get_device_count()
# print(f"检测到音频设备数量：{device_count}")
#
# for i in range(device_count):
#     info = audio.get_device_info_by_index(i)
#     if info.get('maxInputChannels') > 0:
#         print(f"设备索引: {i}, 名称: {info.get('name')}, 输入通道数: {info.get('maxInputChannels')}")
#
# audio.terminate()

parser = argparse.ArgumentParser()
parser.add_argument("--channel", type=int, default=3, help="选择要录制的声道索引（从 0 开始）")
args = parser.parse_args()

FORMAT = pyaudio.paInt16
RATE = 44100
CHUNK = 1024
target_channel_index = args.channel
WAVE_OUTPUT_FILENAME = f"output_ch{target_channel_index + 1}.wav"
audio = pyaudio.PyAudio()

# 指定录音设备索引
device_index = 9
# 动态检测设备支持的最大输入通道数
try:
    device_info = audio.get_device_info_by_index(device_index)
    CHANNELS = int(device_info['maxInputChannels'])
    print(f"🎧 使用设备 {device_index}: {device_info['name']}, 支持通道数: {CHANNELS}")
except Exception as e:
    print("❌ 无法获取设备信息:", e)
    audio.terminate()
    exit(1)
# 开始录音
try:
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=device_index)
except Exception as e:
    print("❌ 无法打开音频流:", e)
    audio.terminate()
    exit(1)
print("Recording...")
frames = []
# 只保存其中一个通道的数据
try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        import numpy as np
        full_audio_np = np.frombuffer(data, dtype=np.int16)
        single_channel = full_audio_np[target_channel_index::CHANNELS]
        data = single_channel.astype(np.int16).tobytes()
        frames.append(data)
except KeyboardInterrupt:
    print("Recording finished.")
# 结束录音
stream.stop_stream()
stream.close()
audio.terminate()
# 保存为 wav 文件
with wave.open(WAVE_OUTPUT_FILENAME,'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
print(f"Audio saved as {WAVE_OUTPUT_FILENAME}")