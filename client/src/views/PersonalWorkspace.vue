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
    <div class="share-status-card" style="margin-bottom: 16px;">
      <template v-if="shareMessage">
        <div class="card-exception">
          <div class="exception-title">
            <span>组员 {{ shareMessage.from_user }} 分享了异常</span>
          </div>
          <div class="exception-detail">
            <span>类型：{{ shareMessage.detail_type }}</span>
            <span style="margin-left: 16px;">状态：{{ shareMessage.detail_status }}</span>
          </div>
          <div class="exception-time">
            <span>收到时间：{{ new Date(shareMessage.receivedAt).toLocaleTimeString() }}</span>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="card-normal">
          <span>当前状态良好，未检测到异常分享</span>
        </div>
      </template>
    </div>
    <el-button
      v-if="showAgendaPanel"
      class="history-feedback-float-btn"
      type="success"
      @click="openHistoryDrawer"
      size="large"
    >
      历史异常反馈
    </el-button>
    <div class="content-container">
      <el-collapse v-model="contentCollapsed">
        <el-collapse-item name="info" class="center-collapse-title">
          <template #title>
            <div class="agenda-header-row" style="position: relative; display: flex; align-items: center;">
              <div class="custom-collapse-title">
                {{ session?.session_title || "议程内容" }}
              </div>
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
        <section class="note-section" style=" width: 100vw; max-width: 100vw;">
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
      </div>
      <el-drawer
        v-model="drawerVisible"
        title="异常反馈"
        :with-header="true"
        size="40%"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <AbnormalFeedback
          v-if="anomalyData"
          :anomaly-data="anomalyData"
        />
      </el-drawer>
      <el-drawer
        v-model="historyDrawerVisible"
        title="历史异常反馈"
        size="60%"
        :with-header="true"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <el-table :data="anomalyHistory" style="width: 100%" v-loading="historyLoading">
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="摘要">
            <template #default="scope">
              <span v-html="scope.row.summary"></span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" @click="viewHistoryDetail(scope.row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-drawer>
      <el-drawer
        v-model="historyDetailDrawerVisible"
        title="异常反馈详情"
        size="50%"
        :with-header="true"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <AbnormalFeedback v-if="historyDetail" :anomaly-data="historyDetail" />
      </el-drawer>
      <div class="analysis-panel">
        <!-- <el-date-picker
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
        > -->
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
import AbnormalFeedback from "@/components/personal/AbnormalFeedback.vue";
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
  ElDrawer,
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
  ElDrawer,
};
const anomalyData = ref(null);
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
const drawerVisible = ref(false);
const historyDrawerVisible = ref(false);
const historyDetailDrawerVisible = ref(false);
const anomalyHistory = ref([]);
const historyDetail = ref(null);
const historyLoading = ref(false);
const shareMessage = ref(null);
const shareMessageTimer = ref(null);

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
  onMessage("share", (payload) => {
    if (!payload || payload.from_user === userId.value) return;
    shareMessage.value = {
      ...payload,
      receivedAt: Date.now(),
    };
    if (shareMessageTimer.value) clearTimeout(shareMessageTimer.value);
    shareMessageTimer.value = setTimeout(() => {
      shareMessage.value = null;
    }, 3 * 60 * 1000);
  });
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  closeWebSocket();
  if (shareMessageTimer.value) clearTimeout(shareMessageTimer.value);
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
  } catch (err) {
    console.error("❌ Interval Summary Error:", err);
  }
}

async function handleAnomalyCheck() {
  console.log("🔍 handleAnomalyCheck 开始执行");
  console.log("📊 当前 selectedUserId.value:", selectedUserId.value);
  console.log("📊 当前 users.value 长度:", users.value.length);
  console.log("📊 users.value 前几个用户:", users.value.slice(0, 3));

  let currentUser = users.value.find((u) => u.id === selectedUserId.value);
  console.log("🔍 找到的当前用户:", currentUser);

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

    if (currentUserById) {
      currentUser = currentUserById;
    } else if (currentUserByUid) {
      currentUser = currentUserByUid;
    }
  }

  const groupId = group.value?.id;
  const roundIndex = currentStage.value || 1;

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
    let parsed = null;
    if (result && result.raw_response) {
      let jsonStr = result.raw_response.trim();
      if (jsonStr.startsWith('```json')) {
        jsonStr = jsonStr.replace(/^```json|```$/g, "").trim();
      }
      try {
        parsed = JSON.parse(jsonStr);
      } catch (e) {
        console.error("❌ 解析异常检测结果失败:", e, jsonStr);
      }
    }
    anomalyData.value = parsed;
    console.log("✅ Anomaly Data:", parsed);
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

watch(anomalyData, (val) => {
  drawerVisible.value = !!val;
});

function openHistoryDrawer() {
  if (!group.value?.id || !userId.value) return;
  historyDrawerVisible.value = true;
  historyLoading.value = true;
  api.getAnomalyResultsByUser(group.value.id, userId.value)
    .then(res => {
      anomalyHistory.value = res.results || [];
    })
    .finally(() => {
      historyLoading.value = false;
    });
}

function viewHistoryDetail(row) {
  let parsed = null;
  if (row && row.raw_response) {
    let jsonStr = row.raw_response.trim();
    if (jsonStr.startsWith('```json')) {
      jsonStr = jsonStr.replace(/^```json|```$/g, '').trim();
    }
    try {
      parsed = JSON.parse(jsonStr);
    } catch (e) {
      console.error('❌ 解析历史异常 raw_response 失败:', e, jsonStr);
    }
  }
  historyDetail.value = parsed;
  historyDetailDrawerVisible.value = true;
}

function formatDate(str) {
  if (!str) return '';
  const d = new Date(str);
  return d.toLocaleString();
}

function saveUserToChromeStorage(userId, userName) {
  if (!window.chrome || !window.chrome.storage) {
    console.warn("chrome.storage 不可用");
    return;
  }
  window.chrome.storage.local.get(['pluginData'], (result) => {
    const pluginData = result.pluginData || {};
    pluginData.user = {
      user_id: userId,
      name: userName,
    };
    window.chrome.storage.local.set({ pluginData }, () => {
      console.log("已写入 pluginData.user:", pluginData.user);
    });
  });
}

watch([
  selectedUserId,
  () => route.params.name,
  users
], ([newUserId, routeName, userList]) => {
  if (!newUserId || !userList.length) return;
  let currentUser = userList.find(u => u.id === newUserId || u.user_id === newUserId || u.uid === newUserId);
  const userName = routeName || currentUser?.name || "";
  saveUserToChromeStorage(newUserId, userName);
}, { immediate: true });
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
  display: block;
  width: 100vw;
  background-color: #fff;
  border-radius: 10px;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.feedback-section,
.note-section {
  flex: 1;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  min-height: 500px;
}

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
  margin-left: 150x;
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
.note-section {
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  min-height: 500px;
  width: 100vw;
  max-width: 100vw;
  margin: 0;
  padding: 0;
}
.feedback-section {
  width: 0;
  height: 0;
  padding: 0;
  margin: 0;
  overflow: visible;
}
.history-feedback-float-btn {
  position: fixed;
  right: 32px;
  top: 80px;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(52,120,246,0.12);
}
::v-deep.center-collapse-title .el-collapse-item__header {
  justify-content: center;
}
.share-status-card {
  width: 100%;
  max-width: 900px;
  margin: 0 auto 16px auto;
  padding: 16px 24px;
  border-radius: 10px;
  background: #f6faff;
  box-shadow: 0 2px 8px rgba(52,120,246,0.08);
  font-size: 1.1rem;
}
.card-exception {
  color: #d35400;
}
.exception-title {
  font-weight: bold;
  font-size: 1.15em;
  margin-bottom: 6px;
}
.exception-detail {
  margin-bottom: 4px;
}
.exception-time {
  font-size: 0.95em;
  color: #888;
}
.card-normal {
  color: #16a085;
  font-weight: 600;
  font-size: 1.1em;
}
</style>
