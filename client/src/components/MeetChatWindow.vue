<template>
  <div :style="$attrs.style">
    <el-scrollbar
      ref="chatWindow"
      class="chat-window"
      @mouseup="handleTextSelection"
    >
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
              <div class="ai-feedback-wrapper">
                <AiFeedback
                  v-if="
                    groupId &&
                    sessionId &&
                    userId &&
                    botId &&
                    msg.msgid &&
                    getBotModel(msg.chatbot_id)
                  "
                  :key="`${msg.msgid}-${msg.created_at}`"
                  :groupId="groupId"
                  :sessionId="sessionId"
                  :userId="userId"
                  :botId="botId"
                  :model="getBotModel(msg.chatbot_id)"
                  promptType="cognitive_guidance"
                  :promptVersion="promptVersion"
                  :targetId="msg.msgid"
                />
              </div>
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

    <!-- 🔍 查询按钮 -->
    <el-button
      v-if="showQueryButton && props.agentId"
      class="query-btn"
      @click="querySelectedText"
      :style="{ top: buttonPosition.y + 'px', left: buttonPosition.x + 'px' }"
    >
      🔍 查询
    </el-button>

    <!-- 📌 查询结果浮窗 -->
    <el-dialog
      v-model="showQueryDialog"
      title="查询结果"
      width="50%"
      @close="handleDialogClose"
    >
      <div v-if="parsedQueryResult">
        <h2 class="term-title">{{ selectedText }}</h2>
        <h3>📖 术语定义</h3>
        <p>{{ parsedQueryResult.definition }}</p>

        <h3 v-if="parsedQueryResult.cross_discipline_insights.length > 0">
          🔍 跨学科洞见
        </h3>
        <ul v-if="parsedQueryResult.cross_discipline_insights.length > 0">
          <li
            v-for="(
              insight, index
            ) in parsedQueryResult.cross_discipline_insights"
            :key="'insight-' + index"
          >
            {{ insight }}
          </li>
        </ul>

        <h3 v-if="parsedQueryResult.application_examples.length > 0">
          💡 应用示例
        </h3>
        <ul v-if="parsedQueryResult.application_examples.length > 0">
          <li
            v-for="(example, index) in parsedQueryResult.application_examples"
            :key="'example-' + index"
          >
            {{ example }}
          </li>
        </ul>
      </div>
      <p v-else>正在查询...</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, defineEmits } from "vue";
import api from "../services/apiService";
import UserInfoPopover from "./UserInfoPopover.vue";
import AiFeedback from "./AiFeedback.vue";
import { playTextWithAzure } from "../services/azureSpeech";

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
  agentId: String, // ✅ 新增 agentId
  botId: String, // ✅ 新增 botId，用于统一传入的 AI 机器人 ID
  promptVersion: String,
  agentModel: String,
  insightsResponse: Function, // ✅ 新增 insightsResponse 回调
  onCloseQueryDialog: {
    type: Function,
    required: false,
  },
  isTtsPlaying: {
    type: Boolean,
    default: false,
  },
});

// ✅ 选中的文本
const selectedText = ref("");
const showQueryButton = ref(false);
const buttonPosition = ref({ x: 0, y: 0 });
const showQueryDialog = ref(false);
const queryResult = ref("");
const isTtsPlaying = ref(false); // ✅ 新增

// ✅ 解析 `queryResult` 并转换成易读的格式
const parsedQueryResult = computed(() => {
  if (!queryResult.value || queryResult.value.trim() === "") {
    return null; // ✅ 避免解析空字符串
  }
  try {
    const cleanJson = queryResult.value
      .replace(/^```json\s*/i, "")
      .replace(/```$/, "");
    const data = JSON.parse(cleanJson);
    if (!data || !data.term_explanation) return null;
    return {
      term_name: data.term_name || "",
      definition: data.term_explanation.definition || "暂无定义。",
      cross_discipline_insights:
        data.term_explanation.cross_discipline_insights || [],
      application_examples: data.term_explanation.application_examples || [],
    };
  } catch (error) {
    console.error("解析查询结果失败:", error);
    return null; // ✅ 解析失败时返回 null，避免页面崩溃
  }
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
  async (newMessages) => {
    scrollToBottom();
    const latestMsg = newMessages.at(-1);
    const msgId = latestMsg?.msgid || latestMsg?.msgId;
    console.log("🎧 Checking new message:", {
      id: latestMsg?.id,
      chatbot_id: latestMsg?.chatbot_id,
      msgid: msgId,
      message: latestMsg?.message,
      alreadySpoken: spokenBotMessageIds.has(msgId),
    });
    if (
      latestMsg &&
      Boolean(latestMsg.chatbot_id) &&
      latestMsg.message &&
      msgId &&
      !spokenBotMessageIds.has(msgId) &&
      newMessages.length > 1 // ✅ Avoid on first render
    ) {
      try {
        emit("stop-audio-capture"); // 🔇 Stop ASR before TTS
        console.log("🛑 Emitting stop-audio-capture before TTS playback");
        isTtsPlaying.value = true; // ✅ 设置 TTS 播放状态
        console.log("🔁 Updating isTtsPlaying to true");
        emit("update:isTtsPlaying", true); // ✅ 向父组件发出 TTS 播放状态
        console.log(
          "🗣️ Playing bot message via Azure TTS...",
          latestMsg.message
        );
        await playTextWithAzure(latestMsg.message, true);
        isTtsPlaying.value = false; // ✅ 重置 TTS 播放状态
        console.log("🔁 Updating isTtsPlaying to false");
        emit("update:isTtsPlaying", false); // ✅ 向父组件发出 TTS 播放状态
        console.log("✅ Speech playback succeeded.");
      } catch (err) {
        isTtsPlaying.value = false; // ✅ 重置 TTS 播放状态
        emit("update:isTtsPlaying", false); // ✅ 向父组件发出 TTS 播放状态
        console.error("❌ Speech playback failed:", err);
      }
      spokenBotMessageIds.add(msgId);
    }
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

// ✅ 监听文本选择
const handleTextSelection = (event) => {
  const selection = window.getSelection().toString().trim();

  if (selection && props.agentId) {
    selectedText.value = selection;
    showQueryButton.value = true;

    // 📌 设置查询按钮位置
    buttonPosition.value = {
      x: event.pageX + 10,
      y: event.pageY - 30,
    };
  } else {
    showQueryButton.value = false;
  }
};

const querySelectedText = async () => {
  if (
    !selectedText.value ||
    !props.groupId ||
    !props.userId ||
    !props.sessionId
  )
    return;

  showQueryDialog.value = true;
  queryResult.value = ""; // 清空旧数据

  try {
    const response = await api.queryDiscussionInsights({
      group_id: props.groupId,
      session_id: props.sessionId,
      user_id: props.userId,
      message_text: selectedText.value,
      ai_provider: props.aiProvider || "-", // 默认使用 xAI
      agent_id: props.agentId, // ✅ 新增
      prompt_version: props.promptVersion,
      model: props.aiProvider,
    });

    queryResult.value = response.insight_text; // 获取 AI 解释的术语

    const insights = await api.getDiscussionInsightsByGroupAndAgent(
      props.groupId,
      props.agentId
    );
    if (props.insightsResponse) {
      props.insightsResponse(insights);
    }
  } catch (error) {
    queryResult.value = "查询失败，请稍后重试。";
    console.error("查询失败:", error);
  }

  showQueryButton.value = false; // 关闭查询按钮
};

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

// ✅ 处理对话框关闭事件
const handleDialogClose = () => {
  if (props.onCloseQueryDialog) {
    props.onCloseQueryDialog(); // 通知父组件已关闭查询弹窗
  }
};
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

/* 🔍 查询按钮 */
.query-btn {
  position: absolute;
  background: #409eff;
  color: white;
  padding: 6px 12px;
  font-size: 14px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease-in-out;
}

.query-btn:hover {
  background: #55a2ef;
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
.ai-feedback-wrapper {
  display: flex;
  justify-content: flex-start;
  margin-top: -10px;
  margin-bottom: 3px;
}

/* 新增术语标题样式 */
.term-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #2c3e50;
}
</style>
