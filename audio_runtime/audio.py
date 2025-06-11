import pyaudio

import wave
from pathlib import Path

import numpy as np
import pyaudio
from resemblyzer import VoiceEncoder, preprocess_wav


def list_audio_devices():
    """列出所有音频输入设备"""
    audio = pyaudio.PyAudio()
    device_count = audio.get_device_count()
    print(f"检测到音频设备数量：{device_count}")

    for i in range(device_count):
        info = audio.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            print(f"设备索引: {i}, 名称: {info.get('name')}, 输入通道数: {info.get('maxInputChannels')}")

    audio.terminate()


def record_audio(device_index, output_filename):
    """录制音频并保存为 WAV 文件"""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    audio = pyaudio.PyAudio()

    # 开始录音
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK,
                        input_device_index=device_index)
    print("Recording...")
    frames = []
    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        print("Recording finished.")
    # 结束录音
    stream.stop_stream()
    stream.close()
    audio.terminate()
    # 保存为 wav 文件
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print(f"Audio saved as {output_filename}")


def similarity_check(wav1_path, wav2_path):
    """计算两个音频文件的相似度"""
    # 加载音频并提取 embedding
    encoder = VoiceEncoder()
    wav1 = preprocess_wav(Path(wav1_path))
    wav2 = preprocess_wav(Path(wav2_path))
    embed1 = encoder.embed_utterance(wav1)
    embed2 = encoder.embed_utterance(wav2)

    # 计算余弦相似度
    similarity = np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))
    print(f"相似度: {similarity:.3f}")

if __name__ == '__main__':

    # 列出音频设备
    # list_audio_devices()

    # 录制音频
    # device_index = 1 # 替换为实际的设备索引
    # output_filename = "output.wav"
    # record_audio(device_index, output_filename)

    # 计算相似度
    similarity_check("p1.wav", "p1-1.wav")