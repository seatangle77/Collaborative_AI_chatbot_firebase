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
      <div class="main-content-layout">
        <div class="left-panel">
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
        </div>
        
        <div class="right-panel">
          <div class="members-status-card">
            <div class="members-status-list">
              <div 
                v-for="member in memberStatusList" 
                :key="member.user_id" 
                class="member-status-item"
              >
                <div class="member-avatar">
                  <span
                    class="collaborator-avatar"
                    :style="{ backgroundColor: getAvatarColor(member) }"
                    :title="member.name"
                  >
                    {{ member.name?.charAt(0) || 'U' }}
                  </span>
                </div>
                <div class="member-info">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-status">
                    <el-tag v-if="member.status === 'abnormal'" type="danger" size="small">
                      异常：{{ member.detail_type }}（{{ member.detail_status }}）
                    </el-tag>
                    <el-tag v-else type="success" size="small">正常</el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="meetingStarted"
        id="jitsi-container"
        class="meeting-container"
      />
      <div class="section-row">
        <div class="note-history-layout">
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
              :editor-started="editorStarted"
            />
          </section>
          <AnomalyHistoryPanel
            :user-id="userId"
            :group-id="group?.id"
            @view-detail="handleViewDetail"
            class="history-panel"
          />
        </div>
      </div>
      <el-drawer
        v-model="drawerVisible"
        :title="drawerSource === 'history' ? '历史异常反馈' : '实时异常反馈'"
        size="50%"
        :with-header="true"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <AbnormalFeedback v-if="drawerData" :anomaly-data="drawerData" />
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
import AnomalyHistoryPanel from '@/components/personal/AnomalyHistoryPanel.vue';
import api from "../services/apiService";
import { connectGroupWebSocket, onGroupMessage, closeGroupWebSocket } from '@/services/groupWebSocket';
import { connectUserWebSocket, onUserMessage, closeUserWebSocket, userWsStatus } from '@/services/userWebSocket';
import {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
  ElDrawer,
  ElAvatar,
  ElTag,
} from "element-plus";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/date-picker/style/css";
import "element-plus/es/components/collapse/style/css";
import "element-plus/es/components/avatar/style/css";
import "element-plus/es/components/tag/style/css";
import { VideoCamera, Warning } from "@element-plus/icons-vue";
import { useRoute } from "vue-router";

const components = {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
  VideoCamera,
  ElDrawer,
  ElAvatar,
  ElTag,
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

const abnormalMap = ref({}); // { user_id: { detail_type, detail_status, timer } }

// 颜色分配与协作笔记一致
const avatarColors = [
  "#f94144", "#f3722c", "#f8961e", "#f9844a",
  "#f9c74f", "#90be6d", "#43aa8b", "#577590"
];
function getAvatarColor(user) {
  if (user.color) return user.color;
  // hash name or id
  const str = user.user_id || user.id || user.name || "";
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return avatarColors[Math.abs(hash) % avatarColors.length];
}

// 过滤出当前用户外的其他组员
const otherMembers = computed(() => {
  return members.value.filter(member => member.user_id !== userId.value);
});
const meetingStarted = ref(false);
const jitsiApi = ref(null);
const activeTab = ref("note");
const currentStage = ref(null);
const agendaList = ref([]);
const showAgendaPanel = ref(false);
const contentCollapsed = ref(["info"]);
const route = useRoute();
const drawerVisible = ref(false);
const drawerData = ref(null);
const drawerSource = ref('history'); // 'history' or 'realtime'
const historyDrawerVisible = ref(false);
const anomalyHistory = ref([]);
const historyDetail = ref(null);
const historyLoading = ref(false);
const shareMessage = ref(null);
const shareMessageTimer = ref(null);
const editorStarted = ref(false);

// 1. 新增分页相关变量
const historyPage = ref(1);
const historyPageSize = ref(10);
const historyTotal = ref(0);

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
  
  // 连接个人ws，只有 userId 有值时才连接
  watch(userId, (newUserId) => {
    if (newUserId) {
      connectUserWebSocket(newUserId);
    }
  }, { immediate: true });
  // 监听个人ws状态
  watch(userWsStatus, (status) => {
    console.log('[userWs] 连接状态:', status);
  });
  // 监听个人ws消息
  onUserMessage("share", (payload) => {
    if (!payload || payload.from_user === userId.value) return;
    // 设置异常
    const uid = payload.from_user;
    if (abnormalMap.value[uid] && abnormalMap.value[uid].timer) {
      clearTimeout(abnormalMap.value[uid].timer);
    }
    const timer = setTimeout(() => {
      abnormalMap.value[uid] = null;
      abnormalMap.value = { ...abnormalMap.value };
    }, 3 * 60 * 1000);
    abnormalMap.value[uid] = {
      detail_type: payload.detail_type,
      detail_status: payload.detail_status,
      receivedAt: Date.now(),
      timer
    };
    abnormalMap.value = { ...abnormalMap.value };
  });
  onUserMessage("anomaly_analysis", (payload) => {
    console.log("📨 收到异常分析结果推送:", payload);
    if (!payload || !payload.data) {
      console.warn("⚠️ 异常分析结果数据格式不正确");
      return;
    }
    handleAnomalyAnalysisResult(payload.data);
    loadHistoryData();
  });

  onUserMessage("personal_task_started", (payload) => {
    editorStarted.value = true;
    showAgendaPanel.value = true;
    if (session.value?.id) {
      api.getAgendas(session.value.id).then(agendas => {
        agendaList.value = agendas;
      });
    }
  });

  // 连接群组ws
  watch(group, (newGroup) => {
    if (newGroup && newGroup.id) {
      connectGroupWebSocket(newGroup.id);
    }
  }, { immediate: true });
  // 监听群组ws消息
  onGroupMessage("agenda_stage_update", (data) => {
    editorStarted.value = true;
    const stage = data.stage;
    currentStage.value = stage;
    if (session.value?.id) {
      api.getAgendas(session.value.id).then(agendas => {
        if (agendas && agendas.length === 1) {
          agendaList.value = agendas;
          showAgendaPanel.value = stage === 1;
        } else {
          showAgendaPanel.value = false;
        }
      });
    }
  });
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  closeGroupWebSocket();
  closeUserWebSocket();
  if (shareMessageTimer.value) clearTimeout(shareMessageTimer.value);
  Object.values(abnormalMap.value).forEach(v => v && v.timer && clearTimeout(v.timer));
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
    }
    memberList.value =
      context.members?.map((m) => ({ id: m.user_id, name: m.name })) || [];
    console.log("👥 当前小组成员列表:", memberList.value.slice());
    
    // 自动加载历史异常反馈数据
    loadHistoryData();
  } catch (error) {
    console.error("❌ 获取用户上下文失败:", error);
    user.value = {};
    group.value = null;
    session.value = null;
    bot.value = null;
  }
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
  if (val) {
    historyDetail.value = null; // 清除历史详情，显示实时异常
    drawerVisible.value = true;
  }
});

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
  drawerVisible.value = true;
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

// 组员面板数据
const memberStatusList = computed(() => {
  return members.value
    .filter(member => member.user_id !== userId.value)
    .map(member => {
      const abnormal = abnormalMap.value[member.user_id];
      return {
        ...member,
        abnormal,
        status: abnormal ? 'abnormal' : 'normal',
        detail_type: abnormal?.detail_type,
        detail_status: abnormal?.detail_status
      };
    });
});

function handleAnomalyAnalysisResult(data) {
  console.log("📨 处理异常分析结果:", data);
  // 解析异常分析结果
  let parsedData = null;
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data);
    } catch (e) {
      console.error("❌ 解析异常分析结果失败:", e);
      return;
    }
  } else {
    parsedData = data;
  }
  // 补全 group_id、user_id、anomaly_analysis_results_id
  drawerData.value = {
    ...parsedData,
    group_id: group.value?.id,
    user_id: userId.value,
    anomaly_analysis_results_id: parsedData.anomaly_analysis_results_id || parsedData.id || parsedData.result_id || ""
  };
  drawerSource.value = 'realtime';
  drawerVisible.value = true;
}

// 2. 修改 loadHistoryData 方法，支持分页
function loadHistoryData(page = historyPage.value, pageSize = historyPageSize.value) {
  if (!group.value?.id || !userId.value) return;
  historyLoading.value = true;
  api.getAnomalyResultsByUser(group.value.id, userId.value, page, pageSize)
    .then(res => {
      anomalyHistory.value = res.results || [];
      historyTotal.value = res.total || 0;
      historyPage.value = res.page || 1;
      historyPageSize.value = res.page_size || 10;
    })
    .catch(err => {
      console.error("❌ 加载历史异常反馈失败:", err);
    })
    .finally(() => {
      historyLoading.value = false;
    });
}

// 3. 分页事件
function onHistoryPageChange(page) {
  historyPage.value = page;
  loadHistoryData(page, historyPageSize.value);
}
function onHistoryPageSizeChange(size) {
  historyPageSize.value = size;
  historyPage.value = 1;
  loadHistoryData(1, size);
}

function handleViewDetail(detail) {
  drawerData.value = {
    ...detail,
    group_id: group.value?.id,
    user_id: userId.value,
    anomaly_analysis_results_id: detail.id || detail.anomaly_analysis_results_id || detail.result_id || ""
  };
  drawerSource.value = 'history';
  drawerVisible.value = true;
}

watch(agendaList, (newList) => {
  if (newList && newList.length > 0) {
    contentCollapsed.value = ['info'];
  }
});
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

.main-content-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  width: 100%;
  margin: 0 auto;
  padding: 0 20px;
  background:#fff;
}

.left-panel {
  flex: 3;
  min-width: 0;
}

.right-panel {
  flex: 1;
  min-width: 280px;
  max-width: 320px;
}

.members-status-card {
  background: #ffffff;
  padding: 16px;
  position: sticky;
  top: 20px;
}

.members-status-header {
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 12px;
  color: #303133;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 8px;
}

.members-status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.member-status-item:hover {
  background-color: #f5f7fa;
  border-color: #c0c4cc;
}

.member-avatar {
  flex-shrink: 0;
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #303133;
}

.member-status {
  display: flex;
  align-items: center;
}

.share-message-card {
  width: 100%;
  max-width: 900px;
  margin: 0 auto 16px auto;
  padding: 16px 24px;
  border-radius: 10px;
  background: #f6faff;
  box-shadow: 0 2px 8px rgba(52,120,246,0.08);
  font-size: 1.1rem;
}

.share-message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.share-message-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-message-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.share-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  font-weight: bold;
}

.value {
  color: #303133;
}

.share-details {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.share-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.share-message-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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

.note-history-layout {
  display: flex;
  gap: 20px;
  margin: 0 auto;
  padding: 0 20px;
}

.note-section {
  flex: 3;
  min-width: 0;
}

.history-panel {
  flex: 1;
  min-width: 300px;
  max-width: 400px;
}

.note-title-wrapper,
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 46px;
  padding: 0 0 8px 0;
  margin-bottom: 16px;
  box-sizing: border-box;
}

.note-title,
.history-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.5;
  display: flex;
  align-items: center;
  height: 100%;
}

.note-title-wrapper .el-button,
.history-header .el-button {
  margin-left: 16px;
  height: 32px;
  line-height: 32px;
  padding: 0 16px;
  display: flex;
  align-items: center;
}

.history-content {
  height: calc(100vh - 400px);
  min-height: 400px;
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

.agenda-panel {
  width: 100% !important;
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

::v-deep.center-collapse-title .el-collapse-item__header {
  border-top: none !important;
  border-bottom: none !important;
}
::v-deep.center-collapse-title .el-collapse-item__wrap {
  border-bottom: none !important;
}
:deep(.el-collapse) {
  border: none !important;
  box-shadow: none !important;
}
.custom-collapse-title{
color: #555;
font-size: 1.1rem;
text-align: center;
width: 75vw;
}

.collaborator-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: white;
}

.note-title,
.history-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.5;
}
</style>
