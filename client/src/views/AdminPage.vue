<template>
  <div class="admin-page">
    <header>
      <GroupHeader
        v-if="group"
        :group="group"
        :members="filteredMembers"
        :goal="sessionName"
        :session-id="selectedSessionId"
        :session-title="selectedSessionTitle"
        :all-groups="groups"
        :selected-group-id="selectedGroupId"
        :bot="selectedBot"
        @update-group="selectGroup"
      />
      <StageTimeline
        :agenda-items="agendaItems"
        :session-id="selectedSessionId"
        :group-id="selectedGroupId || ''"
        :current-index="currentStage"
        v-model:currentIndex="currentStage"
        @select-stage="handleStageSelect"
      />
    </header>
    <div class="content-container">
      <main class="main-content">
        <SpeechLogPanel :speechData="speechData" />
        <BehaviorLogPanel :behaviorData="behaviorData" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watchEffect } from "vue";
import api from "../services/apiService";
import GroupHeader from "@/components/admin/GroupHeader.vue";
import StageTimeline from "@/components/admin/StageTimeline.vue";
import SpeechLogPanel from "@/components/admin/SpeechLogPanel.vue";
import BehaviorLogPanel from "@/components/admin/BehaviorLogPanel.vue";

const group = ref(null);
const session = ref(null);
const agenda = ref({ items: [] });
const bot = ref(null);
const members = ref([]);
const users = ref({});
const groups = ref([]);
const selectedGroupId = ref(null);

const speechData = ref([]);
const behaviorData = ref([]);

const currentStage = ref(-1);

function handleStageSelect(index) {
  currentStage.value = index;
}

const currentTask = computed(() => {
  return agenda.value.items?.[currentStage.value]?.task || "";
});

const currentDescription = computed(() => {
  return agenda.value.items?.[currentStage.value]?.agenda_description || "";
});

const allocatedTime = computed(() => {
  return agenda.value.items?.[currentStage.value]?.allocated_time_minutes || 0;
});

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
  members.value = memberList.map((m) => users.value[m.user_id]).filter(Boolean);

  await fetchSessionAndData(groupId);
};

const aiBots = ref([]);
const selectedBot = computed(() =>
  aiBots.value.find((b) => b.group_id === selectedGroupId.value)
);
bot.value = selectedBot;

const selectedSessionId = computed(() => session.value?.id || "");
const selectedSessionTitle = computed(() => session.value?.session_title || "");
const sessionName = computed(() => group.value?.group_goal || "");
const filteredMembers = computed(() =>
  members.value.map((m) => users.value[m.user_id] || m).filter(Boolean)
);

onMounted(async () => {
  groups.value = await api.getGroups();
  aiBots.value = await api.getAiBots();
  if (!groups.value.length) return;

  const defaultGroupId = groups.value[0].id;
  await selectGroup(defaultGroupId);
});

// 调试输出 agenda.value.items 变化
watchEffect(() => {
  console.log(
    "📋 agenda.value.items from parent (AdminPage):",
    agenda.value.items
  );
});

// 统一处理 agenda 数据传递
const agendaItems = computed(() => agenda.value.items || []);
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100vw;
  margin: 0 auto;
  box-sizing: border-box;
}

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

main.main-content {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  flex: 1;
}

.speech-panel,
.behavior-panel {
  width: 50%;
  min-height: 700px;
  font-size: 16px;
}
</style>
