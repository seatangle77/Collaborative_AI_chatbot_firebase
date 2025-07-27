<template>
  <div class="public-screen">
    <div class="content-container">
      <div class="full-width-block">
        <el-collapse v-model="contentCollapsed">
          <GroupOverview
            v-if="group"
            :group="group"
            :members="filteredMembers"
            :goal="sessionName"
            :session-id="selectedSessionId"
            :session-title="selectedSessionTitle"
            :all-groups="groups"
            :selected-group-id="selectedGroupId"
    
            @update-group="selectGroup"
            :route-name="route.params.name"
          />
          <el-collapse-item name="info">
            <template #title>
              <div class="custom-collapse-title">
                {{ selectedSessionTitle }}
              </div>
            </template>
            <div class="header-row"></div>
            <StartMeetingPanel
              v-if="!showAgendaPanel"
              @start-meeting="startMeeting"
            />
            <div v-if="showAgendaPanel" class="agenda-panel flex-row">
              <div
                v-for="agenda in agendaList"
                :key="agenda.id"
                class="agenda-flex-row"
              >
                <div class="agenda-left">
                  <div class="agenda-task-prompt">
                    {{ agenda.agenda_title }}
                  </div>
                  <div
                    class="agenda-desc"
                    v-html="formatAgendaDesc(agenda.agenda_description)"
                  ></div>
                </div>
                <div class="agenda-right">
                  <div class="output-req-row">
                    <div
                      v-for="(req, key) in agenda.output_requirements"
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
                <div v-if="agenda.allocated_time_minutes" class="agenda-timer-bar">
                  <div style="width: 100%; height: 18px; background: #eee; border-radius: 9px; overflow: hidden; margin: 8px 0;">
                    <div :style="{
                      width: (
                        agendaTimers[agenda.id]?.finished
                          ? '100%'
                          : (100 * (1 - (agendaTimers[agenda.id]?.timeLeft || 0) / (agenda.allocated_time_minutes * 60))) + '%'
                    ),
                    height: '100%',
                    background: '#3478f6',
                    transition: 'width 0.5s'
                  }"></div>
                  </div>
                  <transition name="fade">
                    <div v-if="!agendaTimers[agenda.id]?.finished" class="timer-warning">
                      剩余时间：{{ formatTime(agendaTimers[agenda.id]?.timeLeft) }}
                    </div>
                  </transition>
                  <transition name="fade">
                    <div v-if="agendaTimers[agenda.id]?.finished" class="agenda-finished-tip">
                      🎉 任务已完成！
                    </div>
                  </transition>
                  <el-button
                    type="danger"
                    size="large"
                    style="margin-top: 15px; padding: 12px 24px; font-size: 16px; font-weight: 600;"
                    :loading="anomalyPollingLoading"
                    :disabled="anomalyPollingStopped"
                    @click="stopAnomalyPolling"
                  >
                    🛑 停止所有功能
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div class="content-inner">
        <main class="main-content">
          <!-- Jitsi 会议容器已移除 -->
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue";
import GroupOverview from "@/components/public/GroupOverview.vue";
import api from "../services/apiService";
import { ElButton, ElCollapse, ElCollapseItem } from "element-plus";
import "element-plus/es/components/button/style/css";
import { VideoCamera } from "@element-plus/icons-vue";
import StartMeetingPanel from "@/components/public/StartMeetingPanel.vue";
import { useRoute } from "vue-router";
import apiService from '../services/apiService';
// 移除 groupWebSocketManager 相关导入
// import { connectGroupSocket, sendGroupMessage } from "@/services/groupWebSocketManager";

const components = { ElButton, ElCollapse, ElCollapseItem, VideoCamera };


const group = ref(null);
const users = ref({});
const groupMembers = ref([]);
const groups = ref([]);
const selectedGroupId = ref(null);
const sessionName = ref("");
const selectedSessionId = ref(null);
const selectedSessionTitle = ref("");
const agendaList = ref([]);
const showAgendaPanel = ref(false);
const contentCollapsed = ref(["info"]);


const route = useRoute();

const filteredMembers = computed(() => {
  if (!users.value || !groupMembers.value.length) return [];
  return groupMembers.value.map((uid) => users.value[uid]).filter(Boolean);
});

const anomalyPollingLoading = ref(false);
const anomalyPollingStopped = ref(false);

const selectGroup = async (groupId) => {
  selectedGroupId.value = groupId;
  const groupData = groups.value.find((g) => g.id === groupId);
  if (!groupData) return;
  group.value = groupData;
  const userList = await api.getUsers();
  users.value = userList.reduce((acc, user) => {
    acc[user.user_id] = user;
    return acc;
  }, {});
  const memberList = await api.getGroupMembers(groupId);
  groupMembers.value = memberList.map((m) => m.user_id);
  sessionName.value = groupData.group_goal || "";

  // 获取 session 并设置 sessionTitle
  let session = null;
  try {
    session = await api.getSession(groupId);
    selectedSessionId.value = session.id;
    selectedSessionTitle.value = session.session_title;
  } catch (e) {
    selectedSessionId.value = null;
    selectedSessionTitle.value = "";
  }
  // agendaList 不自动获取
  agendaList.value = [];
};

async function startMeeting() {
  // 只有点击开始时才获取议程
  if (selectedSessionId.value) {
    try {
      const agendas = await api.getAgendas(selectedSessionId.value);
      agendaList.value = agendas || [];
      showAgendaPanel.value = true;
      // 调用重置议程状态接口，并加日志
      console.log('[startMeeting] 调用 resetAgendaStatus', selectedGroupId.value, 1);
      await api.resetAgendaStatus(selectedGroupId.value, 1);
      // 新增：启动AI异常分析轮询
      anomalyPollingLoading.value = true;
      anomalyPollingStopped.value = false;
      try {
        await apiService.startAnomalyPolling(selectedGroupId.value);
        // 移除 groupWebSocketManager 相关导入
        // 移除 connectGroupSocket(selectedGroupId.value) 和 sendGroupMessage(selectedGroupId.value, ...) 的调用
      } catch (e) {
        // 可选：处理异常
      }
      anomalyPollingLoading.value = false;
    } catch (e) {
      agendaList.value = [];
      showAgendaPanel.value = false;
    }
  }
}

async function stopAnomalyPolling() {
  anomalyPollingLoading.value = true;
  try {
    // 停止异常分析轮询
    await apiService.stopAnomalyPolling(selectedGroupId.value);
    anomalyPollingStopped.value = true;
    
    // 停止所有议程计时器
    stopAllAgendaTimers();
    
    console.log('已停止异常分析轮询和所有计时器');
  } catch (e) {
    console.error('停止操作失败:', e);
  }
  anomalyPollingLoading.value = false;
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

// 新增：进度条与倒计时相关
const agendaTimers = ref({}); // { agendaId: { timeLeft, interval, finished } }

function startAgendaTimer(agenda) {
  if (!agenda.allocated_time_minutes) return;
  const totalSeconds = agenda.allocated_time_minutes * 60;
  if (!agendaTimers.value[agenda.id]) {
    agendaTimers.value[agenda.id] = {
      timeLeft: totalSeconds,
      interval: null,
      finished: false,
    };
  }
  if (agendaTimers.value[agenda.id].interval) return;
  agendaTimers.value[agenda.id].interval = setInterval(() => {
    if (agendaTimers.value[agenda.id].timeLeft > 0) {
      agendaTimers.value[agenda.id].timeLeft--;
    } else {
      agendaTimers.value[agenda.id].finished = true;
      clearInterval(agendaTimers.value[agenda.id].interval);
      agendaTimers.value[agenda.id].interval = null;
      // 新增：自动触发停止所有功能
      if (!anomalyPollingStopped.value) {
        stopAnomalyPolling();
      }
    }
  }, 1000);
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function stopAllAgendaTimers() {
  Object.keys(agendaTimers.value).forEach(agendaId => {
    const timer = agendaTimers.value[agendaId];
    if (timer.interval) {
      clearInterval(timer.interval);
      timer.interval = null;
    }
  });
  console.log('所有议程计时器已停止');
}

watch(agendaList, (newList) => {
  // 新议程数据时，启动所有计时器
  if (Array.isArray(newList)) {
    newList.forEach((agenda) => {
      console.log('agenda id:', agenda.id, 'allocated_time_minutes:', agenda.allocated_time_minutes);
      if (agenda.allocated_time_minutes) {
        startAgendaTimer(agenda);
      }
    });
  }
});

// 移除 group ws 监听日志

onMounted(async () => {
  // 打印路由参数 name
  console.log("路由参数 name:", route.params.name);
  groups.value = await api.getGroups();
  if (!groups.value.length) return;
  const defaultId = groups.value[0].id;
  await selectGroup(defaultId);
});
</script>

<style scoped>
.public-screen {
  width: 100vw;
  min-height: 100vh;
  background: #fff;
  padding: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.content-container {
  width: 100vw;
  margin: 0;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  align-items: center;
  background: #fff;
}

.full-width-block {
  width: 100vw;
  background: transparent;
  box-sizing: border-box;
  display: block;
  margin-bottom: 0;
}

.el-collapse {
  width: 100vw;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100vw;
  margin-top: 0;
  background: #fff;
  border-radius: 0;
  box-shadow: none;
  box-sizing: border-box;
  padding: 0 10px 0 10px;
  align-items: flex-start;
}

.page-header > *:first-child {
  width: 100%;
}

.page-header .goal {
  font-size: 1.2rem;
  font-weight: 700;
  color: #3478f6;
  margin-left: 12px;
}

.content-inner {
  width: 100vw;
  margin: 0;
  box-sizing: border-box;
  display: block;
  background: #fff;
  padding: 0;
}

.main-content {
  width: 100vw;
  padding: 0;
  margin: 0;
  display: block;
}

.task-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

@media (max-width: 600px) {
  .page-header,
  .content-inner,
  .start-meeting-panel {
    width: 100vw;
    padding-left: 0;
    padding-right: 0;
  }
}



.agenda-panel {
  width: 100%;
  margin: 0 auto;
  background: #fff;
  padding: 0 20px 0 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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

.agenda-card {
  width: 80%;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 10px 24px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  margin-top: 12px;
}

.header-row {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
}
.content-toggle-btn {
  margin: 12px 5vw 0 0;
  z-index: 3;
}

/* 居中 el-collapse-item 标题（适配 Element Plus 内部组件，需用 ::v-deep） */
::v-deep(.el-collapse-item__header) {
  justify-content: center !important;
  text-align: center !important;
  font-size: 1.1rem;
  color: #555;
}
.custom-collapse-title {
  width: 100%;
  text-align: center;
  font-size: 1.1rem;
  color: #555;
  font-weight: 500;
}

.agenda-panel.flex-row {
  display: flex;
  flex-direction: column;
  width: auto;
  align-items: flex-start;
  justify-content: center;
}
.agenda-flex-row {
  display: flex;
  flex-direction: column;
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

::v-deep(.el-collapse-item__wrap) {
  margin: 0;
}

.agenda-timer-bar {
  width: 100%;
  margin-bottom: 10px;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.timer-warning {
  color: #e67e22;
  font-size: 1.15rem;
  font-weight: bold;
  margin-top: 4px;
  animation: blink 1s step-end infinite alternate;
}
@keyframes blink {
  0% { opacity: 1; }
  100% { opacity: 0.5; }
}
.agenda-finished-tip {
  color: #67c23a;
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 8px;
  animation: pop 0.5s;
}
@keyframes pop {
  0% { transform: scale(0.7); opacity: 0; }
  80% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); }
}

.output-req-row ul {
  margin: 0;
  padding-left: 18px;
  font-size: 0.98em;
  line-height: 1.4;
}

.output-req-row ul li {
  margin-bottom: 2px;
  padding: 0;
}
</style>
