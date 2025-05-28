<template>
  <div :style="$attrs.style">
    <el-scrollbar ref="chatWindow" class="chat-window">
      <div class="chat-list">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="chat-message"
          :class="{ 'ai-message': msg.chatbot_id }"
        >
          <template v-if="msg.chatbot_id">
            <div class="wechat-bubble ai-message">
              <div class="sender">{{ getSenderName(msg) }}</div>
              <div class="message-content">{{ msg.message }}</div>
              <div class="timestamp">{{ formatTimestamp(msg.created_at) }}</div>
            </div>
          </template>
          <template v-else>
            <div class="wechat-message">
              <UserInfoPopover :userInfo="usersInfo[msg.user_id]">
                <img
                  v-if="usersInfo[msg.user_id]?.avatar_link"
                  :src="usersInfo[msg.user_id].avatar_link"
                  class="avatar-circle"
                  alt="avatar"
                />
              </UserInfoPopover>
              <div class="wechat-bubble">
                <div class="sender">
                  {{ usersInfo[msg.user_id]?.name || "👤 未知用户" }}
                </div>
                <div class="message-content">{{ msg.message }}</div>
                <div class="timestamp">
                  {{ formatTimestamp(msg.created_at) }}
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, defineEmits } from "vue";
import UserInfoPopover from "./UserInfoPopover.vue";

const emit = defineEmits();

const props = defineProps({
  messages: Array,
  users: Object,
  usersInfo: Object,
  aiBots: { type: Array, default: () => [] },
  groupId: String,
  sessionId: String, // ✅ 新增 sessionId
  userId: String, // ✅ 新增 userId
  aiProvider: String, // ✅ 新增 aiProvider
  botId: String, // ✅ 新增 botId，用于统一传入的 AI 机器人 ID
  onCloseQueryDialog: {
    type: Function,
    required: false,
  },
});

// ✅ 获取消息发送者名称
const getSenderName = (msg) => {
  if (msg.chatbot_id) {
    const bot = props.aiBots.find((bot) => bot.id === msg.chatbot_id);
    return bot ? `🤖 ${bot.name}` : "🤖 AI 机器人";
  }
  return props.users?.[msg.user_id]
    ? `${props.users[msg.user_id]}`
    : "👤 未知用户";
};

// ✅ 格式化时间
const formatTimestamp = (timestamp) => {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// ✅ 绑定滚动条
const chatWindow = ref(null);

// ✅ 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value?.setScrollTop) {
      const wrapRef = chatWindow.value.wrapRef;
      if (wrapRef) {
        chatWindow.value.setScrollTop(wrapRef.scrollHeight);
      }
    }
  });
};

// ✅ 监听消息变化
const spokenBotMessageIds = new Set();
watch(
  () => props.messages,
  (newMessages) => {
    scrollToBottom();
    // TTS playback code removed
  },
  { deep: true }
);

// ✅ 监听消息变化并获取缺失的 msgid
watch(
  () => props.messages,
  async (newMessages) => {
    const latestMsg = newMessages.at(-1);
    const rawLatest = JSON.parse(JSON.stringify(latestMsg));
    const msgId = latestMsg.msgid || latestMsg.msgId;
    if (msgId) {
      latestMsg.msgid = `${msgId}`; // normalize for reactivity
    }
  },
  { deep: true }
);

// ✅ 获取机器人模型
const getBotModel = (botId) => {
  const bot = props.aiBots?.find((b) => b.id === botId);
  return bot?.model || "unknown";
};

// ✅ 监听 aiProvider 变化
watch(
  () => props.aiProvider,
  (newVal, oldVal) => {
    console.log(`🧠 aiProvider changed: ${oldVal} → ${newVal}`);
    // 可根据新的 AI 供应商执行其他逻辑
  }
);
</script>

<style scoped>
/* 🔹 Chat Window 样式 */
.chat-window {
  height: calc(100vh - 70%);
  background: #f9f9f9;
  padding: 10px 15px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid #ddd;
}

/* 🔹 消息列表 */
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

/* 🔹 单条消息 */
.chat-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  color: #333;
  padding: 0;
  border-radius: 0;
  background: none;
  box-shadow: none;
}

/* 🔹 AI 机器人消息（突出显示） */
.ai-message {
  background: #e3f2fd; /* 轻柔蓝色背景 */
}

/* 🔹 发送者名字 */
.sender {
  font-weight: bold;
  color: #409eff;
  cursor: pointer;
}

/* 🔹 AI 机器人名字（更亮眼） */
.wechat-bubble.ai-message .sender {
  color: #1565c0; /* 深蓝色 */
}

/* 🔹 消息内容 */
.message-content {
  flex: 1;
  word-break: break-word;
}

/* 🔹 时间戳 */
.timestamp {
  font-size: 12px;
  color: #aaa;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.avatar-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  margin-right: 6px;
}

.avatar-emoji {
  font-size: 20px;
  margin-right: 6px;
}

/* 新增微信样式 */
.wechat-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.wechat-bubble {
  display: flex;
  flex-direction: column;
  background: #fff; /* 保留非机器人消息背景为白色 */
  padding: 6px 10px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  max-width: 100%;
  flex: 1;
}

.wechat-bubble.ai-message {
  background: #e3f2fd;
  border-left: 4px solid #409eff;
}

.wechat-bubble.ai-message .sender {
  color: #1565c0;
}

.wechat-bubble.ai-message .message-content {
  color: #1e3a8a;
}

.wechat-bubble .sender {
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 2px;
  color: #555;
}

.wechat-bubble .message-content {
  font-size: 14px;
  color: #333;
  word-break: break-word;
}

.wechat-bubble .timestamp {
  font-size: 12px;
  color: #aaa;
  align-self: flex-end;
  margin-top: 4px;
}

/* 新增 AI 反馈样式 */
</style>
