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
            <!-- 保留议程标题和描述，以及计时器和停止按钮 -->
            <div v-if="showAgendaPanel && agendaList.length > 0" class="agenda-panel">
              <div v-for="agenda in agendaList" :key="agenda.id" class="agenda-content">
                <!-- 紧凑的议程布局 -->
                <div class="compact-agenda-layout">
                  <!-- 议程描述 -->
                  <div class="agenda-description-compact" v-html="formatAgendaDesc(agenda.agenda_description)"></div>
                  
                  <!-- 输出要求 - 紧凑版本 -->
                  <div v-if="agenda.output_requirements" class="output-requirements-compact">
                    <div class="compact-title">📋 输出要求</div>
                    <div class="requirements-grid">
                      <div v-if="agenda.output_requirements.findings" class="requirement-item">
                        <div class="req-title">{{ agenda.output_requirements.findings.title }}</div>
                        <div class="req-desc">{{ agenda.output_requirements.findings.instructions }}</div>
                      </div>
                      <div v-if="agenda.output_requirements.proposals" class="requirement-item">
                        <div class="req-title">{{ agenda.output_requirements.proposals.title }}</div>
                        <div class="req-desc">{{ agenda.output_requirements.proposals.instructions }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-collapse-item>
          
          <!-- 计时器和停止按钮 - 放在 el-collapse-item 外面 -->
          <div v-if="showAgendaPanel && agendaList.length > 0" class="timer-section">
            <div v-for="agenda in agendaList.filter(a => a.allocated_time_minutes)" :key="`timer-${agenda.id}`" class="agenda-timer-bar">
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
              <div class="timer-controls">
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
                  style="padding: 12px 24px; font-size: 16px; font-weight: 600;"
                  :loading="anomalyPollingLoading"
                  :disabled="anomalyPollingStopped"
                  @click="stopAnomalyPolling"
                >
                  🛑 停止所有功能
                </el-button>
              </div>
            </div>
          </div>
          <!-- 新增：实时编辑协作展示区域 -->
          <div v-if="showAgendaPanel && filteredMembers.length > 0" class="collaboration-section">
            <div class="collaboration-panel">
              <div class="multi-note-editors">
                <div 
                  v-for="member in filteredMembers" 
                  :key="member.user_id" 
                  class="member-editor-container"
                >
                  <div class="editor-header">
                    <div class="member-info">
                      <div class="member-avatar" :style="{ backgroundColor: getMemberColor(member) }">
                        {{ member.name?.charAt(0) || 'U' }}
                      </div>
                      <div class="member-details">
                        <div class="member-name">{{ member.name }}</div>
                        <div class="member-status">
                          <span class="status-dot online"></span>
                          在线编辑中
                        </div>
                      </div>
                    </div>
                    <div class="editor-badge readonly">
                      只读展示
                    </div>
                  </div>
                  
                  <NoteEditor
                    :note-id="`note-${selectedGroupId}-${member.user_id}`"
                    :user-id="member.user_id"
                    :members="filteredMembers"
                    :editor-started="true"
                    :read-only="true"
                    :show-title="false"
                    :current-user-id="member.user_id"
                  />
                </div>
              </div>
            </div>
          </div>
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
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import GroupOverview from "@/components/public/GroupOverview.vue";
import NoteEditor from "@/components/personal/NoteEditor.vue";
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
const contentCollapsed = ref(["info", "collaboration"]);


const route = useRoute();

const filteredMembers = computed(() => {
  if (!users.value || !groupMembers.value.length) return [];
  return groupMembers.value.map((uid) => users.value[uid]).filter(Boolean);
});

// 新增：计算总字数
const totalWordCount = computed(() => {
  // 这里可以后续添加实时字数统计逻辑
  return filteredMembers.value.length * 0; // 暂时返回0，后续可以通过WebSocket获取实时字数
});

// 新增：获取成员颜色
const getMemberColor = (member) => {
  const colors = [
    "#f94144", "#f3722c", "#f8961e", "#f9844a", 
    "#f9c74f", "#90be6d", "#43aa8b", "#577590"
  ];
  const str = member.user_id || member.id || member.name || "";
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

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
const agendaTimers = ref({}); // { agendaId: { timeLeft, interval, finished, startTime } }

function startAgendaTimer(agenda) {
  if (!agenda.allocated_time_minutes) return;
  const totalSeconds = agenda.allocated_time_minutes * 60;
  
  if (!agendaTimers.value[agenda.id]) {
    agendaTimers.value[agenda.id] = {
      timeLeft: totalSeconds,
      interval: null,
      finished: false,
      startTime: Date.now(),
      totalSeconds: totalSeconds
    };
  }
  
  if (agendaTimers.value[agenda.id].interval) return;
  
  agendaTimers.value[agenda.id].interval = setInterval(() => {
    const timer = agendaTimers.value[agenda.id];
    if (!timer) return;
    
    // 基于实际经过的时间计算剩余时间，而不是简单的递减
    const elapsedSeconds = Math.floor((Date.now() - timer.startTime) / 1000);
    const newTimeLeft = Math.max(0, timer.totalSeconds - elapsedSeconds);
    
    if (newTimeLeft > 0) {
      timer.timeLeft = newTimeLeft;
    } else {
      timer.finished = true;
      timer.timeLeft = 0;
      clearInterval(timer.interval);
      timer.interval = null;
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
  
  // 添加页面可见性变化监听器
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

// 监听页面可见性变化，确保计时器在页面切换时正常工作
const handleVisibilityChange = () => {
  if (!document.hidden) {
    // 页面重新可见时，更新所有计时器的状态
    Object.keys(agendaTimers.value).forEach(agendaId => {
      const timer = agendaTimers.value[agendaId];
      if (timer && !timer.finished) {
        const elapsedSeconds = Math.floor((Date.now() - timer.startTime) / 1000);
        const newTimeLeft = Math.max(0, timer.totalSeconds - elapsedSeconds);
        timer.timeLeft = newTimeLeft;
        
        // 如果时间已到，标记为完成
        if (newTimeLeft <= 0) {
          timer.finished = true;
          timer.timeLeft = 0;
          if (timer.interval) {
            clearInterval(timer.interval);
            timer.interval = null;
          }
          // 自动触发停止所有功能
          if (!anomalyPollingStopped.value) {
            stopAnomalyPolling();
          }
        }
      }
    });
  }
};

// 页面卸载时清理计时器和事件监听器
onUnmounted(() => {
  stopAllAgendaTimers();
  document.removeEventListener('visibilitychange', handleVisibilityChange);
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
  font-size: 1.2rem;
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

::v-deep(.el-collapse-item__content) {
  padding-bottom: 0px;
}

.agenda-timer-bar {
  width: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.timer-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: auto;
  margin-top: 8px;
  gap: 20px;
}
.timer-warning {
  color: #e67e22;
  font-size: 1.15rem;
  font-weight: bold;
  animation: blink 1s step-end infinite alternate;
  flex: 1;
}
@keyframes blink {
  0% { opacity: 1; }
  100% { opacity: 0.5; }
}
.agenda-finished-tip {
  color: #67c23a;
  font-size: 1.25rem;
  font-weight: bold;
  animation: pop 0.5s;
  flex: 1;
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

/* 新增：协作展示区域样式 */
.collaboration-section {
  width: 100%;
  background: #fff;
  border-top: 1px solid #e4e7ed;
  padding: 20px 0;
}

.collaboration-header {
  padding: 0 20px 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 20px;
}

.collaboration-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  text-align: center;
}

.collaboration-panel {
  width: auto;
  padding: 0px 20px;
  background: #fff;
}

.collaboration-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
}

.collaboration-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.collaboration-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

.stat-value {
  font-size: 1rem;
  font-weight: 600;
  color: #3478f6;
}

.multi-note-editors {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  width: 100%;
}

.member-editor-container {
  background: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.member-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
}

.member-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: #67c23a;
  box-shadow: 0 0 4px rgba(103, 194, 58, 0.4);
}

.editor-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.editor-badge.readonly {
  background: #e6a23c;
  color: white;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .multi-note-editors {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .multi-note-editors {
    grid-template-columns: 1fr;
  }
  
  .collaboration-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .collaboration-stats {
    gap: 15px;
  }
  
  .timer-controls {
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }
  
  .timer-warning,
  .agenda-finished-tip {
    text-align: center;
  }
}

/* 确保NoteEditor在协作展示区域中的样式 */
.member-editor-container :deep(.note-editor) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 添加过渡动画效果 */
.member-editor-container {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.member-editor-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

/* 协作面板的淡入动画 */
.collaboration-panel {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.member-editor-container :deep(.quill-editor) {
  flex: 1;
  min-height: 300px;
}

.member-editor-container :deep(.ql-toolbar) {
  background: #f8f9fa;
  border-bottom: 1px solid #e1e5e9;
}

.member-editor-container :deep(.ql-container) {
  flex: 1;
  overflow-y: auto;
}

.member-editor-container :deep(.ql-editor) {
  min-height: 250px;
  padding: 16px;
}

.task-section {
  padding: 16px 24px 0 24px;
  margin-bottom: 8px;
}
.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.task-title {
  font-size: 20px;
  font-weight: bold;
  color: #222;
}
.collapse-btn {
  font-size: 14px;
  color: #3478f6;
  padding: 0 8px;
}
.task-desc {
  margin: 4px 0 12px 0;
  color: #555;
  font-size: 15px;
  line-height: 1.6;
}
.task-content-row {
  display: flex;
  gap: 24px;
}
.task-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.block-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}
.card {
  background: #fafbfc;
  border-radius: 8px;
  padding: 16px 18px;
  box-shadow: 0 1px 4px #0001;
  font-size: 15px;
}
.card-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 8px;
  color: #333;
}
@media (max-width: 900px) {
  .task-content-row {
    flex-direction: column;
    gap: 12px;
  }
}

/* 新增：任务/输出要求卡片样式 */
.task-output-cards {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  padding: 0 20px;
  width: 100%;
  max-width: 900px;
  justify-content: center;
}

/* 新增：议程面板样式 */
.agenda-panel {
  padding: 0 20px;
  width: auto;
  margin-left: auto;
  margin-right: auto;
}

.agenda-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 0px 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  margin-bottom: 12px;
  width: 100%;
}

.agenda-info {
  margin-bottom: 20px;
}

.agenda-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  text-align: center;
}

.agenda-description {
  font-size: 1rem;
  color: #555;
  line-height: 1.6;
  text-align: left;
}

.output-requirements-card {
  margin-top: 10px;
  background: #fafbfc;
  border-radius: 12px;
  padding: 10px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 95%;
}

.big-card {
  background: #fafbfc;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.big-card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  text-align: center;
}

.big-card-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #3478f6;
  margin-bottom: 6px;
}

.section-desc {
  font-size: 1rem;
  color: #222;
  line-height: 1.6;
  text-align: left;
}

.output-requirement {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.output-requirement:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.example-section {
  margin-top: 8px;
}

.example-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #e67e22;
  margin-bottom: 4px;
}

.example-section ul {
  margin: 0;
  padding-left: 18px;
}

.example-section li {
  margin-bottom: 4px;
}

.example-point {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.example-support {
  color: #666;
  font-size: 0.85rem;
  margin-left: 8px;
}

/* 新增：紧凑议程布局样式 */
.compact-agenda-layout {
  display: flex;
  flex-direction: column;
}

.agenda-description-compact {
  font-size: 0.95rem;
  color: #333;
  line-height: 1.5;
  text-align: left;
  padding: 8px 0;
}

.output-requirements-compact {
  background: #f8f9fa;
  border-radius: 6px;
}

.compact-title {
  font-size: 1rem;
  font-weight: 600;
  color: #3478f6;
  margin-bottom: 8px;
}

.requirements-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.requirement-item {
  background: #fff;
  border-radius: 4px;
  padding: 8px 10px;
  border: 1px solid #e1e5e9;
}

.req-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.req-desc {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .requirements-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

/* 新增：计时器区域样式 */
.timer-section {
  width: auto;
}

.timer-section .agenda-timer-bar {
  padding: 8px;
  background: #f8f9fa;
}

.timer-section .agenda-timer-bar:last-child {
  margin-bottom: 0;
}
</style>
