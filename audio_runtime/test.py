import pyaudio

import wave


audio = pyaudio.PyAudio()
device_count = audio.get_device_count()
print(f"检测到音频设备数量：{device_count}")

for i in range(device_count):
    info = audio.get_device_info_by_index(i)
    if info.get('maxInputChannels') > 0:
        print(f"设备索引: {i}, 名称: {info.get('name')}, 输入通道数: {info.get('maxInputChannels')}")

audio.terminate()