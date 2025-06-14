import pyaudio

p = pyaudio.PyAudio()

print("🎧 可用输入设备列表：\n")

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        print(f"🔹 设备索引: {i}")
        print(f"   名称: {info['name']}")
        print(f"   最大输入通道数: {info['maxInputChannels']}")
        print(f"   默认采样率: {info['defaultSampleRate']}")
        print("-" * 40)

p.terminate()