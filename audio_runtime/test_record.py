import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd

# 检查当前默认输入设备的通道数
default_device = sd.default.device[0]
device_info = sd.query_devices(default_device)
print(f"🎧 默认输入设备: {device_info['name']}")
print(f"🎚️ 支持的最大输入通道数: {device_info['max_input_channels']}")

# 设置聚合设备索引（请替换为你系统中聚合设备的正确 index）
device_index = 6  # 👈 修改为你的聚合设备 index
duration = 10.0
samplerate = 44100


channels = 3  # 显式设置通道数为3
print(f"🧪 使用的通道数: {channels}")

# 在录音前设置默认设备索引
sd.default.device = (device_index, None)

# 检查是否支持3通道输入
try:
    sd.check_input_settings(device=device_index, channels=channels, samplerate=samplerate)
    print("✅ 设备支持该通道数和采样率组合")
except Exception as e:
    print("❌ 设备不支持该通道数和采样率组合，错误：", e)
    exit(1)

# 录制音频
audio = sd.rec(
    int(duration * samplerate),
    samplerate=samplerate,
    channels=channels,
    dtype='int16',
    device=device_index
)
sd.wait()

# 拆分通道
left = audio[:, 0]
right = audio[:, 1]
mac = audio[:, 2]

# 打印样本信息
print("🎙️ RØDE Left 通道样本前20个:", left[:20])
print("🎙️ RØDE Right 通道样本前20个:", right[:20])
print("🎙️ Mac 麦克风通道样本前20个:", mac[:20])

# 可视化三个通道波形
plt.figure(figsize=(12, 5))
plt.plot(left, label='RØDE Left', alpha=0.7)
plt.plot(right, label='RØDE Right', alpha=0.7)
plt.plot(mac, label='Mac Mic', alpha=0.7)
plt.title("三通道音轨波形")
plt.xlabel("采样点")
plt.ylabel("振幅")
plt.legend()
plt.tight_layout()
plt.show()