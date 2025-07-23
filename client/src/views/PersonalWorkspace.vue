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
                <div
                  class="agenda-header-row"
                  style="position: relative; display: flex; align-items: center"
                >
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
                      v-html="
                        formatAgendaDesc(agendaList[0].agenda_description)
                      "
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
                              <div class="example-support">
                                {{ ex.support }}
                              </div>
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

          <div v-if="anomalyData" class="anomaly-feedback-section">
            <AbnormalFeedback :anomaly-data="anomalyData" :members="members" />
          </div>
        </div>


      </div>
      <div
        v-if="meetingStarted"
        id="jitsi-container"
        class="meeting-container"
      />
      <div class="section-row">
        <div class="note-section" style="display: flex; flex-direction: row; width: 99%; height: 100vh; min-height: 0; align-items: stretch;">
          <!-- 多成员编辑器区域：每个人都能看到所有成员的NoteEditor，只能编辑自己的，其他只读 -->
          <div class="multi-note-editors" style="flex: 8; display: flex; flex-direction: row; gap: 20px; height: 100%; min-height: 0; max-width: 80vw;">
            <div v-for="member in members" :key="member.user_id" class="member-editor-flex" style="flex: 1 1 0%; min-width: 0; display: flex; flex-direction: column;">
              <div class="editor-header">
                <span class="editor-title">{{ member.name }} 的工作区</span>
                <span v-if="userId === member.user_id" class="current-user-badge">（你）</span>
                <span v-else class="readonly-badge">只读</span>
              </div>
              <NoteEditor
                :note-id="`note-${group?.id}-${member.user_id}`"
                :user-id="member.user_id"
                :members="members"
                :editor-started="editorStarted && userId === member.user_id"
                :read-only="userId !== member.user_id"
                :show-title="false"
                :current-user-id="userId"
              />
            </div>
          </div>
          <!-- 右侧历史异常反馈区域和两个空白占位区域 -->
          <div class="history-panel-side" style="flex: 2; min-width: 180px; max-width: 20vw; height: 800px; margin-left: 20px; overflow: auto; align-self: flex-start; display: flex; flex-direction: column; gap: 20px;">
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
                      {{ member.name?.charAt(0) || "U" }}
                    </span>
                  </div>
                  <div class="member-info">
                    <div class="member-name">{{ member.name }}</div>
                    <div class="member-status">
                      <div
                        v-if="member.status === 'abnormal'"
                        class="abnormal-detail"
                      >
                        异常：{{ member.detail_type }}（{{
                          member.detail_status
                        }}）
                      </div>
                      <el-tag v-else type="success" size="small">正常</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <AnomalyHistoryPanel
              :user-id="userId"
              :group-id="group?.id"
              @view-detail="handleViewDetail"
              class="history-panel"
            />
          </div>
        </div>
      </div>
      <div v-if="showRichNotification" class="rich-notification">
        <AbnormalFeedback
          v-if="drawerData"
          :anomaly-data="drawerData"
          :members="members"
        />
        <span class="close-btn" @click="showRichNotification = false">×</span>
      </div>
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
import AnomalyHistoryPanel from "@/components/personal/AnomalyHistoryPanel.vue";
import api from "../services/apiService";
import {
  connectGroupSocket,
  onGroupMessage,
  closeGroupSocket,
} from "@/services/groupWebSocketManager";
import {
  connectUserWebSocket,
  onUserMessage,
  closeUserWebSocket,
  userWsStatus,
} from "@/services/userWebSocket";
import {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
  ElDrawer,
  ElAvatar,
  ElTag,
  ElMessage,
  ElTabs,
  ElTabPane,
} from "element-plus";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/date-picker/style/css";
import "element-plus/es/components/collapse/style/css";
import "element-plus/es/components/avatar/style/css";
import "element-plus/es/components/tag/style/css";
import {
  VideoCamera,
  Warning,
  ArrowRight,
  ArrowLeft,
} from "@element-plus/icons-vue";
import { useRoute } from "vue-router";
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';

const components = {
  ElButton,
  ElDatePicker,
  ElCollapse,
  ElCollapseItem,
  VideoCamera,
  ElDrawer,
  ElAvatar,
  ElTag,
  ElTabs,
  ElTabPane,
  ArrowRight,
  ArrowLeft,
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
  "#f94144",
  "#f3722c",
  "#f8961e",
  "#f9844a",
  "#f9c74f",
  "#90be6d",
  "#43aa8b",
  "#577590",
];
function getAvatarColor(user) {
  if (user.color) return user.color;
  // hash name or id
  const str = user.user_id || user.id || user.name || "";
  let hash = 0;
  for (let i = 0; i < str.length; i++)
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return avatarColors[Math.abs(hash) % avatarColors.length];
}

// 过滤出当前用户外的其他组员
const otherMembers = computed(() => {
  return members.value.filter((member) => member.user_id !== userId.value);
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
const drawerSource = ref("history"); // 'history' or 'realtime'
const historyDrawerVisible = ref(false);
const anomalyHistory = ref([]);
const historyDetail = ref(null);
const historyLoading = ref(false);
const editorStarted = ref(false);

// 1. 新增分页相关变量
const historyPage = ref(1);
const historyPageSize = ref(10);
const historyTotal = ref(0);
const activeUserTab = ref("");
const isSummaryExpanded = ref(false);

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
  watch(
    userId,
    (newUserId) => {
      if (newUserId) {
        connectUserWebSocket(newUserId);
      }
    },
    { immediate: true }
  );
  // 监听个人ws状态
  watch(userWsStatus, (status) => {
    console.log("[userWs] 连接状态:", status);
  });
  // 监听个人ws消息
  onUserMessage("share", (payload) => {
    if (!payload || payload.from_user === userId.value) return;

    // 获取发送者姓名
    const fromUser = members.value.find((m) => m.user_id === payload.from_user);
    const fromUserName = fromUser?.name || payload.from_user;

    // 设置异常状态（用于组员状态面板）
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
      timer,
    };
    abnormalMap.value = { ...abnormalMap.value };

    // 显示通知
    ElMessage.info(`${fromUserName} 分享了异常信息：${payload.detail_type}`);
  });
  onUserMessage("anomaly_analysis", (payload) => {
    // 移除调试打印，只保留原有逻辑
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
      api.getAgendas(session.value.id).then((agendas) => {
        agendaList.value = agendas;
      });
    }
  });

  onUserMessage("agenda_stage_update", (data) => {
    // 直接更新当前 group 的议程UI
    editorStarted.value = true;
    const stage = data.stage;
    currentStage.value = stage;
    if (session.value?.id) {
      api.getAgendas(session.value.id).then((agendas) => {
        if (agendas && agendas.length === 1) {
          agendaList.value = agendas;
          showAgendaPanel.value = stage === 1;
        } else {
          showAgendaPanel.value = false;
        }
      });
    }
  });

  // 连接群组ws
  watch(
    group,
    (newGroup) => {
      if (newGroup && newGroup.id) {
        connectGroupSocket(newGroup.id);
      }
    },
    { immediate: true }
  );
  // 监听群组ws消息
  watch(
    group,
    (newGroup) => {
      if (newGroup && newGroup.id) {
        onGroupMessage(newGroup.id, "agenda_stage_update", (data) => {
          editorStarted.value = true;
          const stage = data.stage;
          currentStage.value = stage;
          if (session.value?.id) {
            api.getAgendas(session.value.id).then((agendas) => {
              if (agendas && agendas.length === 1) {
                agendaList.value = agendas;
                showAgendaPanel.value = stage === 1;
              } else {
                showAgendaPanel.value = false;
              }
            });
          }
        });
      }
    },
    { immediate: true }
  );
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  if (group.value && group.value.id) {
    closeGroupSocket(group.value.id);
  }
  closeUserWebSocket();
  Object.values(abnormalMap.value).forEach(
    (v) => v && v.timer && clearTimeout(v.timer)
  );
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

    // 设置默认Tab为当前用户
    activeUserTab.value = newUserId;

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
    console.log("�� 使用 user_id 字段查找:", currentUserById);
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
      if (jsonStr.startsWith("```json")) {
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
  return desc.replace(/\n/g, "<br/>");
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
    if (jsonStr.startsWith("```json")) {
      jsonStr = jsonStr.replace(/^```json|```$/g, "").trim();
    }
    try {
      parsed = JSON.parse(jsonStr);
    } catch (e) {
      console.error("❌ 解析历史异常 raw_response 失败:", e, jsonStr);
    }
  }
  historyDetail.value = parsed;
  drawerVisible.value = true;
}

function formatDate(str) {
  if (!str) return "";
  const d = new Date(str);
  return d.toLocaleString();
}

function saveUserToChromeStorage(userId, userName) {
  if (!window.chrome || !window.chrome.storage) {
    console.warn("chrome.storage 不可用");
    return;
  }
  window.chrome.storage.local.get(["pluginData"], (result) => {
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

watch(
  [selectedUserId, () => route.params.name, users],
  ([newUserId, routeName, userList]) => {
    if (!newUserId || !userList.length) return;
    let currentUser = userList.find(
      (u) =>
        u.id === newUserId || u.user_id === newUserId || u.uid === newUserId
    );
    const userName = routeName || currentUser?.name || "";
    saveUserToChromeStorage(newUserId, userName);
  },
  { immediate: true }
);

// 组员面板数据
const memberStatusList = computed(() => {
  return members.value
    .filter((member) => member.user_id !== userId.value)
    .map((member) => {
      const abnormal = abnormalMap.value[member.user_id];
      return {
        ...member,
        abnormal,
        status: abnormal ? "abnormal" : "normal",
        detail_type: abnormal?.detail_type,
        detail_status: abnormal?.detail_status,
      };
    });
});

function handleAnomalyAnalysisResult(data) {
  console.log("📨 处理异常分析结果:", data);
  // 解析异常分析结果
  let parsedData = null;
  if (typeof data === "string") {
    try {
      parsedData = JSON.parse(data);
    } catch (e) {
      console.error("❌ 解析异常分析结果失败:", e);
      return;
    }
  } else {
    parsedData = data;
  }

  // 确保score字段存在，用于判断是否显示
  if (!parsedData.score) {
    parsedData.score = { should_notify: true };
  }

  // 调试：检查ID字段
  console.log("🔍 [调试] 检查ID字段:");
  console.log(
    "  - anomaly_analysis_results_id:",
    parsedData.anomaly_analysis_results_id
  );
  console.log("  - analysis_id:", parsedData.analysis_id);
  console.log("  - id:", parsedData.id);
  console.log("  - result_id:", parsedData.result_id);

  // 补全 group_id、user_id、anomaly_analysis_results_id
  const anomalyId =
    parsedData.anomaly_analysis_results_id ||
    parsedData.analysis_id ||
    parsedData.id ||
    parsedData.result_id ||
    "";
  console.log("🔍 [调试] 最终使用的ID:", anomalyId);

  drawerData.value = {
    ...parsedData,
    group_id: group.value?.id,
    user_id: userId.value,
    anomaly_analysis_results_id: anomalyId,
  };
  drawerSource.value = "realtime";
  drawerVisible.value = true;
}

// 2. 修改 loadHistoryData 方法，支持分页
function loadHistoryData(
  page = historyPage.value,
  pageSize = historyPageSize.value
) {
  if (!group.value?.id || !userId.value) return;
  historyLoading.value = true;
  api
    .getAnomalyResultsByUser(group.value.id, userId.value, page, pageSize)
    .then((res) => {
      anomalyHistory.value = res.results || [];
      historyTotal.value = res.total || 0;
      historyPage.value = res.page || 1;
      historyPageSize.value = res.page_size || 10;
    })
    .catch((err) => {
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

function toggleSummaryExpand() {
  isSummaryExpanded.value = !isSummaryExpanded.value;
}

function handleViewDetail(detail) {
  // 解析历史记录的raw_response获取完整数据
  let parsedData = null;
  if (detail.raw_response) {
    let jsonStr = detail.raw_response.trim();
    if (jsonStr.startsWith("```json")) {
      jsonStr = jsonStr.replace(/^```json|```$/g, "").trim();
    }
    try {
      parsedData = JSON.parse(jsonStr);
    } catch (e) {
      console.error("❌ 解析历史异常 raw_response 失败:", e, jsonStr);
    }
  }

  // 合并数据，确保兼容性
  drawerData.value = {
    ...parsedData, // 从raw_response解析的完整数据
    ...detail, // 数据库中的字段（会覆盖解析的重复字段）
    group_id: group.value?.id,
    user_id: userId.value,
    anomaly_analysis_results_id:
      detail.id || detail.anomaly_analysis_results_id || detail.result_id || "",
    // 确保score字段存在，用于判断是否显示
    score: parsedData?.score || { should_notify: true },
  };
  drawerSource.value = "history";
  drawerVisible.value = true;
}

watch(agendaList, (newList) => {
  if (newList && newList.length > 0) {
    contentCollapsed.value = ["info"];
  }
});

function unlockBody() {
  document.body.style.overflow = '';
}

// 移除resizable-editor相关逻辑
const showRichNotification = ref(false);

// 替换原有 drawerVisible 控制逻辑：
watch(drawerVisible, (val) => {
  showRichNotification.value = val;
});
watch(showRichNotification, (val) => {
  if (!val) drawerVisible.value = false;
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
  gap: 1rem;
  box-sizing: border-box;
}

.main-content-layout {
  display: flex;
  align-items: flex-start;
  /* margin: 0 auto;  删除居中 */
  background: #fff;
  width: 100vw; /* 新增，铺满页面宽度 */
  box-sizing: border-box;
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
  align-items: flex-start;
  flex-wrap: wrap;
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

.note-section {
  margin: 0 auto;
}

.history-section {
  margin: 0 auto;
  padding: 0 20px;
}

.history-panel {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
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
.custom-collapse-title {
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

.abnormal-detail {
  background: #ffeaea;
  color: #e74c3c;
  border-radius: 6px;
  padding: 8px 12px;
  margin-top: 4px;
  margin-bottom: 4px;
  font-size: 13px;
  word-break: break-all;
  white-space: pre-line;
  max-width: 95%;
}

.note-tabs-layout {
  display: flex;
  gap: 20px;
  align-items: stretch;
  height: 600px;
  min-height: 600px;
  max-height: 600px;
}

.user-notes-tab-container {
  flex: 3;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* --- Summary Note Container Styles (override and ensure no collapse/overflow) --- */
.summary-note-container {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  flex: 1 1 0%;
  min-width: 350px;
  max-width: 400px;
  transition: width 0.3s ease, flex-basis 0.3s ease;
  flex-basis: auto;
}
.summary-note-container.expanded {
  flex: 1 1 50%;
  max-width: 50vw;
  width: 50%;
  flex-basis: 50%;
}

.expand-toggle-btn {
  margin-left: auto;
  padding: 8px 12px;
  color: #606266;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.expand-toggle-btn:hover {
  color: #409eff;
  background-color: #f0f9ff;
}

.user-notes-tabs {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.user-notes-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  flex-shrink: 0;
  order: 1;
}

.user-notes-tabs :deep(.el-tabs__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
  order: 2;
}

.user-notes-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.user-notes-tabs :deep(.el-tabs__nav-wrap) {
  order: 1;
}

.user-notes-tabs :deep(.el-tabs__content) {
  order: 2;
}

.tab-editor-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9f9f9;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.multi-note-editors {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

/* --- Editor Container Styles for Summary (override and ensure no collapse/overflow) --- */
.editor-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  min-width: 320px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #f9f9f9;
  margin-bottom: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.editor-container :deep(.note-editor) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.editor-container :deep(.quill-editor) {
  flex: 1;
  min-height: 200px;
  overflow-y: auto;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
  font-size: 0.6rem;
  font-weight: 300;
  color: #303133;
  min-height: 32px;
  height: 32px;
}

.editor-header .editor-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-user-badge {
  background-color: #409eff;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-left: 10px;
}

.readonly-badge {
  background-color: #e6a23c;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 10px;
}

.editor-container,
.tab-editor-container,
.summary-note-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* 防止flex塌陷 */
}

.note-tabs-layout {
  display: flex;
  gap: 20px;
  align-items: stretch;
  height: 600px;
  min-height: 600px;
  max-height: 600px;
}

.user-notes-tab-container {
  flex: 3;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.summary-note-container {
  flex: 1 1 0%;
  min-width: 350px;
  max-width: 400px;
  transition: width 0.3s ease, flex-basis 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  flex-basis: auto;
}

.summary-note-container.expanded {
  flex: 1 1 50%;
  max-width: 50vw;
  width: 50%;
  flex-basis: 50%;
}

.expand-toggle-btn {
  margin-left: auto;
  padding: 8px 12px;
  color: #606266;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.expand-toggle-btn:hover {
  color: #409eff;
  background-color: #f0f9ff;
}

.user-notes-tabs {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.user-notes-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  flex-shrink: 0;
  order: 1;
}

.user-notes-tabs :deep(.el-tabs__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
  order: 2;
}

.user-notes-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.user-notes-tabs :deep(.el-tabs__nav-wrap) {
  order: 1;
}

.user-notes-tabs :deep(.el-tabs__content) {
  order: 2;
}

.tab-editor-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9f9f9;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.multi-note-editors {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.editor-container {
  flex: 1 1 0%;
  min-width: 320px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9f9f9;
  margin-bottom: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.editor-container :deep(.note-editor) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-container :deep(.quill-editor) {
  flex: 1;
  min-height: 400px;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0px 15px;
  background-color: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
  font-size: 0.8rem;
  font-weight: 600;
  color: #303133;
}

.editor-header .editor-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-user-badge {
  background-color: #409eff;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-left: 10px;
}

.readonly-badge {
  background-color: #e6a23c;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 10px;
}

.editor-container,
.tab-editor-container,
.summary-note-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* 防止flex塌陷 */
  margin-bottom: 0;
}

.note-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* 防止父容器高度塌陷 */
}

.quill-editor {
  flex: 1 1 0%;
  min-height: 200px;
  /* 保持原有样式 */
  display: flex;
  flex-direction: column;
}

.editor-footer {
  flex-shrink: 0;
  padding: 8px 16px;
  font-size: 12px;
  color: #6c757d;
  background: #f8f9fa;
  border-top: 1px solid #e1e5e9;
}

/* Ensure Quill editor's .ql-container expands properly in summary note section */
.editor-container :deep(.ql-container) {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
/* Slightly taller quill editor inside the summary note container */
.summary-note-container :deep(.quill-editor) {
  min-height: 210px;
}
.history-panel-side {
  flex: 0 0 15%;
  min-width: 180px;
  max-width: 260px;
  background: #fff;
  border-radius: 10px;
  margin-left: 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: auto;
  overflow-x: hidden;
}
.history-panel-side, .history-panel-side * {
  box-sizing: border-box;
  max-width: 100%;
}
.member-editor-flex {
  flex: 1 1 0%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: stretch;
}
.tab-editor-container {
  min-height: 0;
}
/* splitpanes 样式微调（可选） */
:deep(.splitpanes__pane) {
  display: flex;
  flex-direction: column;
  min-height: 80px;
}
/* splitpanes 分割条样式美化 */
:deep(.splitpanes__splitter) {
  background: #e0e0e0;
  border-top: 1px solid #bbb;
  border-bottom: 1px solid #fff;
  min-height: 6px;
  cursor: row-resize;
}
:deep(.el-drawer__header) {
  font-size: 18px;
  font-weight: bold;
  color: #222;
  margin-bottom: 5px;
  padding-top: 15px;
}
:deep(.el-drawer__body) {
  padding: 0;
  min-height: 200px;
  margin-top: 5px;
}
.rich-notification {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 360px;
  max-height: 100vh;
  background: #fff;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  border-radius: 8px 0 0 8px;
  z-index: 9999;
  overflow-y: auto;
  padding: 0 0 8px 0;
  animation: float-in .2s;
}
.close-btn {
  position: absolute;
  top: 8px;
  right: 16px;
  font-size: 20px;
  cursor: pointer;
}
@keyframes float-in {
  from { opacity: 0; transform: translateY(30px);}
  to { opacity: 1; transform: translateY(0);}
}
</style>
