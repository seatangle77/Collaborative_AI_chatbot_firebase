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
            :bot="selectedGroupBot"
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
              :jitsi-ready="jitsiReady"
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
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div class="content-inner">
        <main class="main-content">
          <div
            v-if="meetingStarted"
            id="jitsi-container"
            class="meeting-container"
          />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import GroupOverview from "@/components/public/GroupOverview.vue";
import api from "../services/apiService";
import { ElButton, ElCollapse, ElCollapseItem } from "element-plus";
import "element-plus/es/components/button/style/css";
import { VideoCamera } from "@element-plus/icons-vue";
import StartMeetingPanel from "@/components/public/StartMeetingPanel.vue";
import { useRoute } from "vue-router";

const components = { ElButton, ElCollapse, ElCollapseItem, VideoCamera };
const aiBots = ref([]);
const selectedGroupBot = computed(() =>
  aiBots.value.find((bot) => bot.group_id === selectedGroupId.value)
);

const group = ref(null);
const users = ref({});
const groupMembers = ref([]);
const groups = ref([]);
const selectedGroupId = ref(null);
const sessionName = ref("");
const selectedSessionId = ref(null);
const selectedSessionTitle = ref("");
const agendaList = ref([]);
const meetingStarted = ref(false);
const jitsiApi = ref(null);
const showAgendaPanel = ref(false);
const jitsiReady = ref(false);
const contentCollapsed = ref(["info"]);

const route = useRoute();

const filteredMembers = computed(() => {
  if (!users.value || !groupMembers.value.length) return [];
  return groupMembers.value.map((uid) => users.value[uid]).filter(Boolean);
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
      await api.resetAgendaStatus(selectedGroupId.value, 1);
    } catch (e) {
      agendaList.value = [];
      showAgendaPanel.value = false;
    }
  }

  // 插入 Jitsi 视频会议
  if (meetingStarted.value) return;
  meetingStarted.value = true;

  nextTick(() => {
    if (typeof window.JitsiMeetExternalAPI !== "function") {
      console.error("JitsiMeetExternalAPI not loaded.");
      return;
    }

    const domain = "meet.jit.si";
    const roomName = `GroupMeeting_${selectedGroupId.value || "default"}`;
    const options = {
      roomName,
      width: "100vw",
      height: 600,
      parentNode: document.querySelector("#jitsi-container"),
    };

    const api = new window.JitsiMeetExternalAPI(domain, options);
    jitsiApi.value = api;
  });
}

const fetchAllAiBots = async () => {
  try {
    const bots = await api.getAiBots();
    aiBots.value = bots;
  } catch (error) {
    console.error("获取 AI 机器人失败:", error);
  }
};

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

onMounted(async () => {
  // 打印路由参数 name
  console.log("路由参数 name:", route.params.name);
  groups.value = await api.getGroups();
  if (!groups.value.length) return;
  await fetchAllAiBots();
  const defaultId = groups.value[0].id;
  await selectGroup(defaultId);
  // 动态加载 Jitsi external_api.js
  if (!window.JitsiMeetExternalAPI) {
    const script = document.createElement("script");
    script.src = "https://meet.jit.si/external_api.js";
    script.async = true;
    script.onload = () => {
      console.log("✅ Jitsi external_api.js 加载完成");
      jitsiReady.value = true;
    };
    script.onerror = () => {
      console.error("❌ Jitsi external_api.js 加载失败");
    };
    document.body.appendChild(script);
  } else {
    jitsiReady.value = true;
  }
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

.meeting-container {
  width: 100vw;
  /* 高度自适应：减去顶部内容和 agenda 区域高度 */
  flex: 1 1 auto;
  max-height: calc(100vh - 180px);
  height: 80vh;
  margin: 0;
  border-radius: 0;
  overflow: hidden;
  background: #000;
  display: block;
  transition: height 0.3s;
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

::v-deep(.el-collapse-item__wrap) {
  margin: 0;
}
</style>
