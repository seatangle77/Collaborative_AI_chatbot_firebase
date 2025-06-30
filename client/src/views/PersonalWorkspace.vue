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
      :route-name="route.params.name"
    />
    <div class="content-container">
      <el-collapse v-model="contentCollapsed">
        <el-collapse-item name="info">
          <template #title>
            <div class="custom-collapse-title">
              {{ session?.session_title || "议程内容" }}
            </div>
          </template>
          <div
            v-if="showAgendaPanel && agendaList.length === 1"
            class="agenda-panel flex-row"
          >
            <div class="agenda-flex-row">
              <div class="agenda-left">
                <div class="agenda-task-prompt">
                  {{ agendaList[0].agenda_title }}
                </div>
                <div
                  class="agenda-desc"
                  v-html="formatAgendaDesc(agendaList[0].agenda_description)"
                ></div>
              </div>
              <div class="agenda-right">
                <div class="output-req-row">
                  <div
                    v-for="(req, key) in agendaList[0].output_requirements"
                    :key="key"
                    class="output-req-card"
                  >
                    <div class="output-req-title">{{ req.title }}</div>
                    <div class="output-req-instructions">
                      {{ req.instructions }}
                    </div>
                    <div
                      v-if="req.example && req.example.length"
                      class="output-req-example"
                    >
                      <div class="example-title">示例：</div>
                      <ul>
                        <li v-for="(ex, idx) in req.example" :key="idx">
                          <div class="example-point">{{ ex.point }}</div>
                          <div class="example-support">{{ ex.support }}</div>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="workspace-header">
            <p>欢迎来到个人工作区</p>
          </div>
        </el-collapse-item>
      </el-collapse>
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
  onBeforeUnmount,
  nextTick,
  computed,
  watch,
} from "vue";
import CognitiveFeedback from "@/components/personal/CognitiveFeedback.vue";
import NoteEditor from "@/components/personal/NoteEditor.vue";
import UserProfileBar from "@/components/personal/UserProfileBar.vue";
import api from "../services/apiService";
import {
  initWebSocket,
  onMessage,
  closeWebSocket,
} from "../services/websocketManager";
import {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
} from "element-plus";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/date-picker/style/css";
import "element-plus/es/components/collapse/style/css";
import { VideoCamera } from "@element-plus/icons-vue";
import { useRoute } from "vue-router";

const components = {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
  VideoCamera,
};
const aiSummary = ref(null);
const showNoteEditor = ref(true);
const startTime = ref(new Date("2025-06-17T10:00:00"));
const endTime = ref(new Date("2025-06-17T10:07:50"));
const user = ref({});
const users = ref([]);
const selectedUserId = ref("");
const discussionId = "discussion_001";
const group = ref(null);
const session = ref(null);
const bot = ref(null);
const members = ref([]);
const memberList = ref([]);
const userId = computed(() => selectedUserId.value);
const meetingStarted = ref(false);
const jitsiApi = ref(null);
const activeTab = ref("note");
const currentStage = ref(null);
const agendaList = ref([]);
const showAgendaPanel = ref(false);
const contentCollapsed = ref(["info"]);
const route = useRoute();

const handleVisibilityChange = () => {
  if (document.visibilityState === "visible") {
    activeTab.value = "";
    nextTick(() => {
      activeTab.value = "note";
    });
  }
};

onMounted(async () => {
  console.log("路由参数 name:", route.params.name);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  users.value = await api.getUsers();
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  closeWebSocket();
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
    group.value = context.group;
    session.value = context.session;
    bot.value = context.bot;
    members.value = context.members || [];
    sendUserInfoToExtension(newUserId, context);
    if (context.group?.id) {
      console.log("🛰 初始化 WebSocket，groupId:", context.group.id);
      initWebSocket(context.group.id);
      onMessage("agenda_stage_update", async (raw) => {
        try {
          const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
          const stage = parsed?.stage;
          if (typeof stage === "number") {
            currentStage.value = stage;
            if (session.value?.id) {
              const agendas = await api.getAgendas(session.value.id);
              if (agendas && agendas.length === 1) {
                agendaList.value = agendas;
                showAgendaPanel.value = stage === 1;
              } else {
                showAgendaPanel.value = false;
              }
            }
          }
        } catch (err) {
          console.error("❌ WebSocket 消息解析失败:", err, raw);
        }
      });
    }
    memberList.value =
      context.members?.map((m) => ({ id: m.user_id, name: m.name })) || [];
    console.log("👥 当前小组成员列表:", memberList.value.slice());
  } catch (error) {
    console.error("❌ 获取用户上下文失败:", error);
    user.value = {};
    group.value = null;
    session.value = null;
    bot.value = null;
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
  console.log("🔍 handleAnomalyCheck 开始执行");
  console.log("📊 当前 selectedUserId.value:", selectedUserId.value);
  console.log("📊 当前 users.value 长度:", users.value.length);
  console.log("📊 users.value 前几个用户:", users.value.slice(0, 3));

  // 从 users 列表中根据 selectedUserId 找到当前用户
  let currentUser = users.value.find((u) => u.id === selectedUserId.value);
  console.log("🔍 找到的当前用户:", currentUser);

  // 如果没有找到，尝试其他可能的字段名
  if (!currentUser) {
    console.log("⚠️ 使用 id 字段未找到用户，尝试其他字段名...");
    const currentUserById = users.value.find(
      (u) => u.user_id === selectedUserId.value
    );
    const currentUserByUid = users.value.find(
      (u) => u.uid === selectedUserId.value
    );
    console.log("🔍 使用 user_id 字段查找:", currentUserById);
    console.log("🔍 使用 uid 字段查找:", currentUserByUid);

    // 使用找到的用户
    if (currentUserById) {
      currentUser = currentUserById;
    } else if (currentUserByUid) {
      currentUser = currentUserByUid;
    }
  }

  const groupId = group.value?.id;
  const roundIndex = currentStage.value || 1;

  // 确保当前用户信息存在
  const currentUserId =
    currentUser?.id ||
    currentUser?.user_id ||
    currentUser?.uid ||
    selectedUserId.value;
  const currentUserName = currentUser?.name || "";
  const currentUserDeviceToken = currentUser?.device_token || "";

  console.log("🔍 提取的用户信息:");
  console.log("  - currentUserId:", currentUserId);
  console.log("  - currentUserName:", currentUserName);
  console.log("  - currentUserDeviceToken:", currentUserDeviceToken);

  // 验证必要字段
  if (!currentUserId) {
    console.error("❌ 当前用户ID不存在");
    console.error("❌ currentUser?.id:", currentUser?.id);
    console.error("❌ selectedUserId.value:", selectedUserId.value);
    return;
  }

  const payload = {
    group_id: groupId,
    round_index: roundIndex,
    start_time: formatToLocalISO(startTime.value),
    end_time: formatToLocalISO(endTime.value),
    members: memberList.value.slice(),
    current_user: {
      user_id: currentUserId,
      name: currentUserName,
      device_token: currentUserDeviceToken,
    },
  };

  console.log("📤 发送异常检测请求:", JSON.stringify(payload, null, 2));

  try {
    const result = await api.getAnomalyStatus(payload);
    console.log("✅ Anomaly Detection Result:", result);
  } catch (err) {
    console.error("❌ Anomaly Detection Error:", err);
  }
}

function formatAgendaDesc(desc) {
  if (!desc) return "";
  return desc
    .replace(/(任务[：:]?)/g, '<b style="font-size:1.1em;">$1</b>')
    .replace(
      /(建议[：:]?)/g,
      '<b style="font-size:1.1em;color:#3478f6;">$1</b>'
    )
    .replace(
      /(目标[：:]?)/g,
      '<b style="font-size:1.1em;color:#e67e22;">$1</b>'
    )
    .replace(
      /(思考[：:]?)/g,
      '<b style="font-size:1.1em;color:#16a085;">$1</b>'
    )
    .replace(/\\n/g, "<br/>");
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

.el-collapse,
.el-collapse-item,
.custom-collapse-title {
  width: 100% !important;
  box-sizing: border-box;
  font-size: 1.2rem;
  color: #555;
}
.agenda-panel {
  width: 100% !important;
}
.agenda-meta {
  width: 100vw;
  max-width: 900px;
  margin: 0 auto 8px auto;
  display: flex;
  flex-direction: row;
  gap: 1rem;
  justify-content: center;
}
.goal-grey,
.session-grey {
  color: #888;
  font-size: 0.95rem;
  font-weight: 400;
  letter-spacing: 0.3px;
}
.agenda-task-prompt {
  font-size: 1.13rem;
  font-weight: 600;
  color: #222;
  margin-bottom: 12px;
  text-align: left;
  letter-spacing: 0.5px;
  line-height: 1.7;
}
.agenda-desc {
  font-size: 1rem;
  color: #222;
  width: 100%;
  text-align: left;
  line-height: 1.6;
  overflow-y: auto;
}
.agenda-desc b {
  font-weight: 700;
}
.agenda-panel.flex-row {
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: flex-start;
  justify-content: center;
}
.agenda-flex-row {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 98%;
  align-items: stretch;
  justify-content: center;
}
.agenda-left,
.agenda-right {
  background: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  width: 100%;
  font-size: 1rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 10px;
}
.output-req-row {
  display: flex;
  flex-direction: row;
  gap: 24px;
  width: 100%;
  justify-content: center;
  align-items: stretch;
}
.output-req-card {
  margin-bottom: 0;
  background: #fff;
  border-radius: 6px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  font-size: 1rem;
  flex: 1 1 0;
  min-width: 0;
}
.output-req-title {
  font-weight: 700;
  color: #3478f6;
  margin-bottom: 6px;
  font-size: 1.13rem;
}
.output-req-instructions {
  color: #222;
  font-size: 1rem;
  margin-bottom: 8px;
}
.example-title {
  color: #e67e22;
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 1rem;
}
.example-point {
  font-weight: 500;
  color: #222;
  font-size: 1rem;
}
.example-support {
  color: #888;
  font-size: 0.98em;
  margin-left: 8px;
}
</style>
