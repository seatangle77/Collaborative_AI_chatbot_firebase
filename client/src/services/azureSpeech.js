const sdk = window.SpeechSDK;

// Azure Speech Service 配置信息
const AZURE_SUBSCRIPTION_KEY = import.meta.env.VITE_AZURE_SUBSCRIPTION_KEY;
const AZURE_REGION = import.meta.env.VITE_AZURE_REGION;

// 初始化 Speech Config
const speechConfig = sdk.SpeechConfig.fromSubscription(
  AZURE_SUBSCRIPTION_KEY,
  AZURE_REGION
);

// 设置默认语音配置
speechConfig.speechSynthesisVoiceName = "zh-CN-XiaoxiaoNeural"; // 可根据需求更改
speechConfig.speechRecognitionLanguage = "zh-CN"; // 设置为中文普通话

// 创建 Speech Synthesizer
const synthesizer = new sdk.SpeechSynthesizer(speechConfig);

/**
 * 使用 Azure Speech Service 播放语音
 * @param text 要朗读的文本
 * @param shouldSpeak 是否执行朗读
 * @returns Promise
 */
export const playTextWithAzure = (text, shouldSpeak = false) => {
  return new Promise((resolve, reject) => {
    if (!shouldSpeak) {
      console.log("🔇 Speech synthesis skipped.");
      return resolve();
    }
    
    console.log("🧪 Azure TTS: Starting speech synthesis for text:", text);

    synthesizer.speakTextAsync(
      text,
      () => {
        console.log("✅ Azure TTS: Speech synthesis completed.");
        resolve();
      },
      (error) => {
        console.error("❌ Azure TTS: Speech synthesis error:", error);
        reject(error);
      }
    );
  });
};

/**
 * 使用 Azure Speech SDK 从麦克风输入进行语音识别
 * @returns {Promise<string>} - 识别出的文本
 */
export const recognizeSpeechFromMicrophone = (timeoutMs = 3000) => {
  return new Promise((resolve, reject) => {
    const audioConfig = sdk.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);

    let timeoutHandle = setTimeout(() => {
      console.warn("⏱️ 语音识别超时：未检测到讲话");
      recognizer.close();
      resolve(""); // 返回空字符串，表示没说话
    }, timeoutMs);

    recognizer.recognizeOnceAsync(
      (result) => {
        clearTimeout(timeoutHandle);
        if (result.reason === sdk.ResultReason.RecognizedSpeech) {
          resolve(result.text);
        } else {
          console.warn("🔈 Azure 语音识别：用户未说话或未识别，不视为错误");
          resolve("");
        }
      },
      (err) => {
        clearTimeout(timeoutHandle);
        console.error("Recognition failed:", err);
        reject(err);
      }
    );
  });
};