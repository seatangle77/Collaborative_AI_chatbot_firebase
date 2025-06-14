<template>
  <div class="personal-workspace">
    <UserProfileBar
      :all-users="users"
      v-model:selected-user-id="selectedUserId"
      :user="user"
      :group="group"
      :members="members"
      :session="session"
      :bot="bot"
      :agenda="agenda"
    />
    <div class="content-container">
      <header class="workspace-header">
        <p v-if="currentStage === 0 || currentStage === null">
          🚀 讨论即将开始
        </p>
        <p v-else-if="currentAgenda">
          <span style="font-size: 1.2rem"
            >📌 当前议程阶段 {{ currentAgenda.agenda_title }}：</span
          ><br />
          <span class="agenda-description">
            {{ currentAgenda.agenda_description || "（无描述）" }}
          </span>
          <el-button type="primary" icon="VideoCamera" @click="joinMeeting">
            加入会议
          </el-button>
        </p>
        <p v-else-if="currentStage === 5">✅ 所有议程已完成</p>
        <p v-else>⏳ 等待议程阶段更新...</p>
      </header>

      <div
        v-if="meetingStarted"
        id="jitsi-container"
        class="meeting-container"
      />

      <div class="section-row">
        <section class="note-section">
          <NoteEditor
            v-if="group?.note_id && showNoteEditor"
            :key="activeTab"
            :user-id="userId"
            :discussion-id="discussionId"
            :note-id="group.note_id"
            :session="session"
            :bot="bot"
            :members="members"
          />
        </section>
        <section class="feedback-section">
          <CognitiveFeedback
            :stage="currentStage"
            :feedback-data="{
              cognitive: aiSummary?.cognitive || {},
              behavior: aiSummary?.behavior || {},
              attention: aiSummary?.attention || {},
            }"
          />
        </section>
      </div>

      <div class="analysis-panel">
        <el-date-picker
          v-model="startTime"
          type="datetime"
          placeholder="开始时间"
        />
        <el-date-picker
          v-model="endTime"
          type="datetime"
          placeholder="结束时间"
        />
        <el-button type="primary" @click="handleIntervalSummary"
          >Interval Summary</el-button
        >
        <el-date-picker
          v-model="startTime"
          type="datetime"
          placeholder="开始时间"
        />
        <el-date-picker
          v-model="endTime"
          type="datetime"
          placeholder="结束时间"
        />
        <el-button type="danger" @click="handleAnomalyCheck"
          >Anomaly Detection</el-button
        >
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  onMounted,
  watch,
  computed,
  onBeforeUnmount,
  nextTick,
  watchEffect,
} from "vue";
// AI 三维度总结
const aiSummary = ref(null);
// 控制 NoteEditor 显示/隐藏的开关
const showNoteEditor = ref(false);
import CognitiveFeedback from "@/components/personal/CognitiveFeedback.vue";
import NoteEditor from "@/components/personal/NoteEditor.vue";
import UserProfileBar from "@/components/personal/UserProfileBar.vue";
import api from "../services/apiService";
import {
  initWebSocket,
  onMessage,
  closeWebSocket,
} from "../services/websocketManager";

import { ElButton, ElDatePicker } from "element-plus";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/date-picker/style/css";
import { VideoCamera } from "@element-plus/icons-vue";

const components = { ElButton, ElDatePicker, VideoCamera };

const startTime = ref(new Date("2025-06-17T10:00:00"));
const endTime = ref(new Date("2025-06-17T10:07:50"));

const currentStage = ref(null); // 设置为 null 更安全，兼容后续判断

const user = ref({});
const users = ref([]);
const selectedUserId = ref("");
const discussionId = "discussion_001";

const group = ref(null);
const session = ref(null);
const bot = ref(null);
const agenda = ref([]);
const members = ref([]);

const memberList = ref([]);

const userId = computed(() => selectedUserId.value);

const currentAgenda = computed(() => {
  if (
    typeof currentStage.value === "number" &&
    currentStage.value >= 1 &&
    currentStage.value <= agenda.value.length
  ) {
    return agenda.value[currentStage.value - 1];
  }
  return null;
});

const meetingStarted = ref(false);
const jitsiApi = ref(null);

const activeTab = ref("note");

const handleVisibilityChange = () => {
  if (document.visibilityState === "visible") {
    activeTab.value = ""; // 暂时清空 key
    nextTick(() => {
      activeTab.value = "note"; // 重新设置 key 以强制刷新 NoteEditor
    });
  }
};

onMounted(() => {
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});

function joinMeeting() {
  if (!window.JitsiMeetExternalAPI) {
    console.warn("JitsiMeetExternalAPI 未加载，稍后重试...");
    return;
  }

  if (meetingStarted.value) return;

  meetingStarted.value = true;
  nextTick(() => {
    const domain = "meet.jit.si";
    const roomName = `GroupMeeting_${group.value?.id || "default"}`;
    const options = {
      roomName,
      width: "100%",
      height: 500,
      parentNode: document.querySelector("#jitsi-container"),
    };
    const api = new window.JitsiMeetExternalAPI(domain, options);
    jitsiApi.value = api;
  });
}

onMounted(async () => {
  users.value = await api.getUsers();
});

// 修改：定义发送用户信息到插件的函数，接受 newUserId, context 两个参数
function sendUserInfoToExtension(newUserId, context) {
  if (!window || !window.postMessage) return;
  if (!context) return;
  let userName = "";
  let userId = "";
  if (Array.isArray(context.members)) {
    const matchedMember = context.members.find((m) => m.user_id === newUserId);
    if (matchedMember) {
      userName = matchedMember.name || "";
      userId = matchedMember.user_id || "";
    }
  }
  const payload = {
    userName,
    user_id: userId,
    group_id: context.group?.id || "",
    session_id: context.session?.id || "",
  };
  window.postMessage(
    {
      type: "user_data_update",
      payload,
    },
    "*"
  );
  console.log("📤 发送用户信息到插件:", payload);
}

watch(selectedUserId, async (newUserId) => {
  try {
    const context = await api.getUserGroupContext(newUserId);
    user.value = context.user;
    group.value = context.group;
    session.value = context.session;
    bot.value = context.bot;
    members.value = context.members || [];

    sendUserInfoToExtension(newUserId, context);

    if (context.session?.id) {
      try {
        const agendas = await api.getAgendas(context.session.id);
        agenda.value = agendas || [];
      } catch (error) {
        console.error("获取议程失败:", error);
        agenda.value = [];
      }
    }

    if (context.group?.id) {
      console.log("🛰 初始化 WebSocket，groupId:", context.group.id);
      initWebSocket(context.group.id);

      // 避免重复注册，先清理
      onMessage("agenda_stage_update", async (raw) => {
        try {
          console.log("📨 WebSocket 收到原始消息:", raw);
          const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
          const stage = parsed?.stage;
          if (typeof stage === "number") {
            console.log("✅ WebSocket 阶段更新为:", stage);
            currentStage.value = stage;

            // 注册监听器
            watch(currentStage, (newStage, oldStage) => {
              // Removed debug console
            });
          } else {
            console.warn("⚠️ 未解析到合法的 stage:", parsed);
          }
        } catch (err) {
          console.error("❌ WebSocket 消息解析失败:", err, raw);
        }
      });
    }

    memberList.value =
      context.members?.map((m) => ({
        id: m.user_id,
        name: m.name,
      })) || [];
    console.log("👥 当前小组成员列表:", memberList.value.slice());
  } catch (error) {
    console.error("❌ 获取用户上下文失败:", error);
    user.value = {};
    group.value = null;
    session.value = null;
    bot.value = null;
    agenda.value = [];
  }
});

onBeforeUnmount(() => {
  closeWebSocket();
});
// 区间统计按钮点击处理
// 时间格式化函数：将 Date 格式为本地时区的 ISO 字符串（不带 Z、不带偏移）
function formatToLocalISO(datetime) {
  const pad = (num) => String(num).padStart(2, "0");
  const year = datetime.getFullYear();
  const month = pad(datetime.getMonth() + 1);
  const day = pad(datetime.getDate());
  const hour = pad(datetime.getHours());
  const minute = pad(datetime.getMinutes());
  const second = pad(datetime.getSeconds());
  return `${year}-${month}-${day}T${hour}:${minute}:${second}`;
}

async function handleIntervalSummary() {
  const groupId = group.value?.id;
  const roundIndex = currentStage.value || 1;
  const payload = {
    groupId,
    roundIndex,
    startTime: formatToLocalISO(startTime.value),
    endTime: formatToLocalISO(endTime.value),
    members: memberList.value.slice(),
  };
  try {
    const result = await api.getIntervalSummary(
      payload.groupId,
      payload.roundIndex,
      payload.startTime,
      payload.endTime,
      payload.members
    );
    console.log("✅ Interval Summary Result:", result);
    aiSummary.value = result;
  } catch (err) {
    console.error("❌ Interval Summary Error:", err);
  }
}

async function handleAnomalyCheck() {
  const groupId = group.value?.id;
  const roundIndex = currentStage.value || 1;
  const payload = {
    group_id: groupId,
    round_index: roundIndex,
    start_time: formatToLocalISO(startTime.value),
    end_time: formatToLocalISO(endTime.value),
    members: memberList.value.slice(),
  };
  try {
    const result = await api.getAnomalyStatus(payload);
    console.log("✅ Anomaly Detection Result:", result);
  } catch (err) {
    console.error("❌ Anomaly Detection Error:", err);
  }
}
</script>

<style scoped>
.personal-workspace {
  width: 100%;
  min-height: 100vh;
  background-color: #f9fafb;
  box-sizing: border-box;
}

.content-container {
  width: 100vw;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  box-sizing: border-box;
}

.workspace-header {
  width: 100%;
  font-size: 1.25rem;
  font-weight: 600;
  text-align: center;
  padding: 1rem 0;
  background-color: #fff;
  border-radius: 10px;
  box-sizing: border-box;
}

.section-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1rem;
  background-color: #fff;
  width: 100vw;
  border-radius: 10px;
  box-sizing: border-box;
}

.feedback-section,
.note-section {
  flex: 1;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  min-height: 500px;
}
/* 可选：如果希望认知反馈区域略窄，可使用如下设置
.feedback-section { flex: 0.9; }
.note-section { flex: 1.1; }
*/

.meeting-controls {
  width: 100%;
  max-width: 1000px;
  text-align: center;
}

.meeting-controls button {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  background-color: #3478f6;
  color: white;
  border: none;
  border-radius: 6px;
  transition: background-color 0.3s ease;
}
.meeting-controls button:hover {
  background-color: #0056d2;
}
.agenda-title {
  display: block;
  font-weight: 700;
  font-size: 1.15rem;
  color: #111;
  margin-bottom: 0.5rem;
}

.agenda-description {
  display: block;
  font-size: 1rem;
  color: #444;
  line-height: 1.6;
  white-space: pre-wrap;
}

.meeting-container {
  width: 100%;
  max-width: 800px;
  margin: 1rem auto;
  min-height: 500px;
  border-radius: 8px;
  overflow: hidden;
}

.analysis-panel {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  background: #fff;
  border-radius: 10px;
  margin: 0 auto;
  width: fit-content;
}
</style>
