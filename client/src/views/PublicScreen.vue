<template>
  <div class="public-screen">
    <div class="content-container">
      <div class="full-width-block">
        <header class="page-header">
          <GroupOverview
            v-if="group"
            :group="group"
            :members="filteredMembers"
            :goal="sessionName"
            :session-id="selectedSessionId"
            :session-title="selectedSessionTitle"
            :all-groups="groups"
            :selected-group-id="selectedGroupId"
            :bot="selectedGroupBot"
            @update-group="selectGroup"
          />
          <AgendaTimeline
            :agenda-items="agendaList"
            :session-id="selectedSessionId || ''"
            :group-id="selectedGroupId || ''"
            :current-index="currentStage"
            v-model:currentIndex="currentStage"
            @select-stage="handleStageSelect"
          />
        </header>
      </div>

      <div class="content-inner">
        <main class="main-content">
          <CurrentTaskPanel
            :group-id="selectedGroupId || ''"
            :agenda="agendaList"
            :current-index="currentStage"
            :task-detail="currentTask"
            :task-description="currentDescription"
          >
          </CurrentTaskPanel>

          <StageProgressBar
            :current-stage="currentStage"
            :agendas="agendaList"
            :session-id="selectedSessionId"
            :allocated-time="allocatedTime"
          />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import AgendaTimeline from "@/components/public/AgendaTimeline.vue";
import CurrentTaskPanel from "@/components/public/CurrentTaskPanel.vue";
import StageProgressBar from "@/components/public/StageProgressBar.vue";
import GroupOverview from "@/components/public/GroupOverview.vue";
import api from "../services/apiService";

const aiBots = ref([]);
const selectedGroupBot = computed(() =>
  aiBots.value.find((bot) => bot.group_id === selectedGroupId.value)
);

const route = useRoute();

const group = ref(null);
const members = ref([]);
// const goal = ref(""); // removed: goal is now sessionName
const sessionName = ref("");
const agendaList = ref([]);
const currentStage = ref(-1);

watch(currentStage, (newVal, oldVal) => {
  // console.log("🌀 currentStage changed:", oldVal, "→", newVal);
});

const users = ref({});
const groupMembers = ref([]);

const groups = ref([]);
const selectedGroupId = ref(null);

const filteredMembers = computed(() => {
  if (!users.value || !groupMembers.value.length) return [];
  return groupMembers.value.map((uid) => users.value[uid]).filter(Boolean);
});

const currentTask = computed(() => {
  return agendaList.value[currentStage.value]?.task || "";
});

const currentDescription = computed(() => {
  return agendaList.value[currentStage.value]?.agenda_description || "";
});

const allocatedTime = computed(() => {
  return agendaList.value[currentStage.value]?.allocated_time_minutes || 0;
});

function handleStageSelect(index) {
  currentStage.value = index;
  // console.log(currentStage.value);
}

function startMeeting() {
  // console.log("🔔 启动会议插件（Jitsi）");
}

function broadcastTask() {
  // console.log("📢 广播当前任务至所有人");
}

const selectedSessionId = ref(null);
const selectedSessionTitle = ref("");

// 新增：聊天数据和议程数据的获取方法
const fetchChatData = async (groupId) => {
  // 预留方法：可在此调用聊天记录接口或其他小组相关数据
};

const fetchChatAgendas = async (sessionId) => {
  try {
    const agendas = await api.getAgendas(sessionId);
    agendaList.value = agendas || [];
  } catch (error) {
    console.error("获取议程失败:", error);
  }
};

const fetchSessionAndData = async (groupId) => {
  try {
    const session = await api.getSession(groupId);

    selectedSessionId.value = session.id; // ✅ 记录当前 Session ID
    selectedSessionTitle.value = session.session_title;

    await fetchChatData(groupId);
    await fetchChatAgendas(selectedSessionId.value); // ✅ 用 session_id 获取议程
  } catch (error) {
    console.error("获取小组当前 Session 失败:", error);
  }
};

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
  await fetchSessionAndData(groupId);
};

const fetchAllAiBots = async () => {
  try {
    const bots = await api.getAiBots();
    aiBots.value = bots;
  } catch (error) {
    console.error("获取 AI 机器人失败:", error);
  }
};

onMounted(async () => {
  groups.value = await api.getGroups();
  if (!groups.value.length) return;

  await fetchAllAiBots();

  const defaultId = groups.value[0].id;
  await selectGroup(defaultId);
});
</script>

<style scoped>
.public-screen {
  width: 100%;
  min-height: 130vh;
  background: #f9fafb;
  padding: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.content-container {
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
  margin-top: 0;
  background: white;
  box-sizing: border-box;
}

.page-header > *:first-child {
  width: 100%;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
}

.task-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.content-inner {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
.full-width-block {
  width: 100vw;
  background: white;
  box-sizing: border-box;
}
</style>
