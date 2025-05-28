<template>
  <el-container class="chat-container">
    <div class="chat-header-wrapper">
      <ChatHeader
        :groups="groups"
        :selectedGroupId="selectedGroupId"
        :selectedAiProvider="selectedAiProvider"
        :selectedGroupBot="selectedGroupBot"
        :selectedSessionTitle="selectedSessionTitle"
        @selectGroup="selectGroup"
        @changeAiProvider="changeAiProvider"
      />
    </div>
    <el-button
      @click="showAgendaPanel = !showAgendaPanel"
      size="default"
      class="toggle-user-card-button"
      style="display: none"
    >
      <el-icon style="font-size: 20px">
        <component :is="showAgendaPanel ? DArrowLeft : DArrowRight" />
      </el-icon>
    </el-button>
    <el-container class="main-content">
      <el-aside
        class="agenda-panel"
        :class="showAgendaPanel ? 'agenda-expanded' : 'agenda-collapsed'"
        v-show="showAgendaPanel"
      >
        <AgendaDisplay
          :agendas="chatAgendas"
          :groupName="selectedGroupName"
          :groupGoal="
            groups.find((g) => g.id === selectedGroupId)?.group_goal || ''
          "
          :groupId="selectedGroupId"
          :sessionId="selectedSessionId"
          @updateGroupInfo="updateGroupInfo"
          @agendaCompleted="handleAgendaCompleted"
        />
      </el-aside>

      <el-main class="chat-area">
        <MeetChatWindow
          style="height: 200px; overflow-y: auto"
          :messages="messages"
          :users="userNames"
          :usersInfo="filteredUsersInfo"
          :aiBots="aiBots"
          :groupId="selectedGroupId"
          :sessionId="selectedSessionId"
          :userId="selectedUser"
          :aiProvider="selectedAiProvider"
          :botId="selectedGroupBot?.id"
          :promptVersion="promptVersions_cognitive_guidance"
          :isTtsPlaying="isTtsPlaying"
        />
        <MessageInput
          :users="filteredUsersInfo"
          :groupId="selectedGroupId"
          @send-message="sendMessage"
          @stop-audio-capture="stopAudioCapture"
          :isTtsPlaying="isTtsPlaying"
          ref="messageInputRef"
        />
        <div id="jitsi-container" style="height: 74%; margin: 20px 0"></div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import ChatHeader from "../components/ChatHeader.vue";
import { ref, computed, onMounted, watch, nextTick } from "vue";
import api from "../services/apiService";
import MeetChatWindow from "../components/MeetChatWindow.vue";
import MessageInput from "../components/MessageInput.vue";
import AgendaDisplay from "../components/AgendaDisplay.vue";
import {
  createWebSocket,
  sendMessage as sendWebSocketMessage,
  onMessageReceived,
  closeWebSocket,
} from "../services/websocketService";
import { InfoFilled, DArrowLeft, DArrowRight } from "@element-plus/icons-vue";

// ✅ **存储状态**
const messages = ref([]);
const users = ref({});
const chatAgendas = ref([]);
const selectedGroupName = ref("");
const selectedGroupId = ref(null);
const selectedSessionId = ref(null); // ✅ 存储当前 Session ID
const selectedSessionTitle = ref("");
const selectedUser = ref(null);
const groupMembers = ref([]);
const groups = ref([]);
const aiBots = ref([]);
const selectedAiProvider = ref("xai"); // ✅ 默认使用 xAI
const selectedGroupBot = computed(() =>
  aiBots.value.find((bot) => bot.group_id === selectedGroupId.value)
); // 新增计算属性
const promptVersions = ref({}); // 新增代码
const showAgendaPanel = ref(true); // 新增代码
const isInitialLoad = ref(true); // 新增代码
const isTtsPlaying = ref(false);
const messageInputRef = ref(null);

const stopAudioCapture = () => {
  // 可选：调用相关逻辑来停止识别，比如设置 isRecognizing = false;
  if (messageInputRef.value?.stopAudioCapture) {
    messageInputRef.value.stopAudioCapture();
  } else {
    console.warn("⚠️ 未能找到 messageInputRef 或 stopAudioCapture 方法");
  }
};

// ✅ **新增计算属性 promptVersions_cognitive_guidance**
const promptVersions_cognitive_guidance = computed(() => {
  return (
    promptVersions.value.cognitive_guidance?.find((p) => p.is_current)
      ?.template_version || null
  );
});

// ✅ **切换 AI 供应商时自动触发 AI 会议总结**
const changeAiProvider = () => {
  if (!selectedGroupId.value) return;
  if (isInitialLoad.value) {
    isInitialLoad.value = false;
    return;
  }
};

// ✅ **获取所有小组**
const fetchGroups = async () => {
  try {
    const response = await api.getGroups();
    groups.value = response;
    if (groups.value.length > 0) {
      selectGroup(groups.value[0].id);
    }
  } catch (error) {
    console.error("获取小组数据失败:", error);
  }
};

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
    fetchSessionAndData(newGroupId);
  }
});

// ✅ 在页面加载时获取所有 AI 机器人
const fetchAllAiBots = async () => {
  try {
    const bots = await api.getAiBots();
    aiBots.value = bots; // ✅ 存储所有机器人数据
  } catch (error) {
    console.error("获取 AI 机器人失败:", error);
  }
};

// ✅ **获取小组成员**
const fetchGroupMembers = async (groupId) => {
  if (!groupId) return;
  try {
    const memberList = await api.getGroupMembers(groupId);
    groupMembers.value = memberList.map((member) => member.user_id);
  } catch (error) {
    console.error("获取小组成员失败:", error);
  }
};

// ✅ **计算当前小组的用户**
const filteredUsersInfo = computed(() => {
  if (!selectedGroupId.value || !users.value || !groupMembers.value.length)
    return {};
  return Object.fromEntries(
    Object.entries(users.value).filter(([userId]) =>
      groupMembers.value.includes(userId)
    )
  );
});

// ✅ 监听 `filteredUsersInfo`，确保有默认的 `selectedUser`
watch(
  filteredUsersInfo,
  (newUsers) => {
    if (Object.keys(newUsers).length > 0) {
      selectedUser.value = Object.keys(newUsers)[0];
    }
  },
  { immediate: true }
);

// ✅ **切换小组**
const selectGroup = async (groupId) => {
  if (!groupId || groupId === selectedGroupId.value) return;
  selectedGroupId.value = groupId;
  selectedGroupName.value =
    groups.value.find((group) => group.id === groupId)?.name || "";

  closeWebSocket(); // 关闭旧的 WebSocket 连接
  fetchChatData(groupId);
};

// ✅ **获取聊天记录**
const fetchChatHistory = async (groupId) => {
  if (!groupId) return;
  try {
    const messageList = await api.getChatHistory(groupId);
    messages.value = messageList.reverse(); // 让最新的消息显示在底部
  } catch (error) {
    console.error("获取聊天记录失败:", error);
  }
};

// ✅ **获取当前小组的最新 Session，并获取该 Session 相关数据**
const fetchSessionAndData = async (groupId) => {
  try {
    const session = await api.getSession(groupId);

    selectedSessionId.value = session.id; // ✅ 记录当前 Session ID
    selectedSessionTitle.value = session.session_title;

    fetchChatData(groupId);
    fetchChatAgendas(selectedSessionId.value); // ✅ 用 session_id 获取议程
  } catch (error) {
    console.error("获取小组当前 Session 失败:", error);
  }
};

// ✅ **获取议程**
const fetchChatAgendas = async (sessionId) => {
  if (!sessionId) return;
  try {
    const agendas = await api.getAgendas(sessionId);
    chatAgendas.value = agendas;
  } catch (error) {
    console.error("获取聊天议程失败:", error);
  }
};

// ✅ **获取所有用户**
const fetchUsers = async () => {
  try {
    const userList = await api.getUsers();
    users.value = userList.reduce((acc, user) => {
      acc[user.user_id] = user;
      return acc;
    }, {});
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
};

// ✅ **发送消息（字段补全，完整结构）**
const sendMessage = async (payload) => {
  const fullMessage = {
    group_id: payload.group_id,
    session_id: selectedSessionId.value,
    user_id: payload.user_id,
    chatbot_id: "",
    msgid: payload.msgid || crypto.randomUUID(),
    message: payload.message,
    role: payload.role || "user",
    message_type: payload.message_type || "text",
    sender_type: payload.sender_type || "user",
    speaking_duration: payload.speaking_duration || 0,
    created_at: new Date().toISOString(),
  };

  try {
    const response = await api.sendChatMessage(fullMessage);
    console.log("📤 发送消息到数据库:", response);
    messages.value.push(response);
    scrollToBottom();
  } catch (error) {
    console.error("❌ 发送消息失败:", error);
  }
};

// ✅ **WebSocket 监听**
const initWebSocket = (groupId) => {
  if (!groupId) return;
  createWebSocket(groupId);

  onMessageReceived((data) => {
    try {
      console.log("📩 WebSocket 收到数据:", data);

      let parsedData;
      if (typeof data === "string") {
        parsedData = JSON.parse(data);
      } else {
        parsedData = data;
      }

      // ✅ **处理 WebSocket 消息类型**
      if (parsedData.message) {
        let newMessage = parsedData.message;
        if (Array.isArray(newMessage)) {
          newMessage = newMessage[0];
        }
        messages.value.push(newMessage);
        scrollToBottom();
      }
    } catch (error) {
      console.error("❌ WebSocket 消息解析错误:", error, "原始数据:", data);
    }
  });
};

// ✅ **滚动到底部**
const chatWindow = ref(null);
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) {
      chatWindow.value.$el.scrollTop = chatWindow.value.$el.scrollHeight;
    }
  });
};

// ✅ **获取所有聊天数据**
const fetchChatData = async (groupId) => {
  if (!groupId) return;
  await fetchUsers();
  await fetchGroupMembers(groupId);
  await fetchChatHistory(groupId);
  initWebSocket(groupId);
};

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
    // ✅ 更新聊天室标题
    selectedGroupName.value =
      groups.value.find((group) => group.id === newGroupId)?.name || "未知小组";

    // ✅ 更新聊天数据
    fetchChatData(newGroupId);
  }
});

// ✅ **新增计算属性 userNames**
const userNames = computed(() => {
  return Object.fromEntries(
    Object.entries(users.value).map(([id, user]) => [id, user.name])
  );
});

// ✅ **更新小组信息**
const updateGroupInfo = ({ name, goal }) => {
  const group = groups.value.find((g) => g.id === selectedGroupId.value);
  if (group) {
    group.name = name;
    group.group_goal = goal;
    selectedGroupName.value = name;
  }
};

// ✅ **处理 Prompt 加载**
const handlePromptLoaded = (payload) => {
  console.log("📥 Prompt versions loaded from AiBotDrawer:", payload);
  const { botId, ...versions } = payload;
  promptVersions.value = versions; // ✅ 正确处理结构，去掉 botId
};

// ✅ **页面加载时获取小组信息**
onMounted(() => {
  fetchGroups();
  fetchAllAiBots(); // ✅ 这里初始化获取所有机器人

  // 👉 页面加载后为当前选中小组建立 WebSocket 连接
  if (selectedGroupId.value) {
    createWebSocket(selectedGroupId.value);
  }

  // ✅ 动态加载 Jitsi IFrame API 并初始化会议
  const script = document.createElement("script");
  script.src = "https://meet.jit.si/external_api.js";
  script.onload = () => {
    const domain = "meet.jit.si";
    const options = {
      roomName: "MyMeetingRoom",
      width: "100%",
      height: "100%",
      parentNode: document.getElementById("jitsi-container"),
      userInfo: {
        displayName: "Participant",
      },
    };
    new window.JitsiMeetExternalAPI(domain, options);
  };
  document.head.appendChild(script);
});
</script>

<style scoped>
/* 📌 整体布局 */
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.chat-header-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #f5f7fa;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 📌 小组选择器 */
.agenda-panel {
  flex: 0.25;
}
.agenda-display {
  width: 100%;
  padding-left: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

/* 📌 议程标题 */
.agenda-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: bold;
}

.agenda-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 📌 议程列表 - 横向滚动 */
.agenda-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: space-between;
}

/* 📌 议程项 */
.agenda-item {
  flex: 1 1 calc(33.333% - 10px);
  min-width: 250px;
  max-width: 400px;
  padding: 15px;
  border-radius: 10px;
  background: #f8f9fa;
  transition: background 0.3s ease;
}

.agenda-item:hover {
  background: #eef5ff;
}

/* 📌 主内容区域 */
.main-content {
  display: flex;
  flex-direction: row;
  flex: 1;
  margin-top: 80px; /* 为 header 留出空间，避免被遮挡 */
}

/* 📌 聊天区域 */
.chat-area {
  flex: 0.75;
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  min-height: 400px; /* 确保聊天窗口不会因为议程太长而变得太小 */
}

/* 📌 AI 实时总结面板 */

/* 📌 议程面板状态 */
.agenda-collapsed {
  display: none;
}

.agenda-expanded {
  display: block;
}
.toggle-user-card-button {
  position: fixed;
  top: 120px;
  left: 0;
  z-index: 999;
  background-color: #ffffff;
  border: 1px solid #dcdfe6;
  padding: 50px 5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  border-radius: 0 6px 6px 0;
}
</style>
