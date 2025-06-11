<template>
  <div v-if="currentIndex !== -1 && agenda.length > 0" class="task-panel">
    <div class="task-header">
      <el-icon><Document /></el-icon>
      <div class="task-title">当前任务</div>
    </div>
    <p class="task-info">{{ taskDescription }}</p>
    <el-button type="primary" @click="startMeeting">启动会议</el-button>

    <div v-if="showMeeting" class="jitsi-container" id="jitsi-container"></div>
  </div>
  <div v-else class="task-panel">
    <div class="task-header">
      <el-icon><Document /></el-icon>
      <div class="task-title">欢迎加入讨论</div>
    </div>
    <p class="task-info">点击开始按钮以解锁议程任务。</p>
  </div>
</template>

<script setup>
import { Document } from "@element-plus/icons-vue";
import { computed, ref, onMounted, nextTick, watch } from "vue";

const props = defineProps({
  currentIndex: {
    type: Number,
    required: true,
  },
  agenda: {
    type: Array,
    required: true,
  },
  groupId: {
    type: String,
    required: true,
  },
});

const currentTask = computed(() => props.agenda[props.currentIndex] || {});
const taskDescription = computed(
  () => currentTask.value.agenda_description || "暂无任务说明"
);

const hasStarted = computed(() => props.currentIndex !== -1);

const showMeeting = ref(false);
// 用于保存 Jitsi 实例
const jitsiApi = ref(null);

function startMeeting() {
  if (!window.JitsiMeetExternalAPI) {
    console.warn("JitsiMeetExternalAPI 未加载，等待 500ms 重试...");
    setTimeout(startMeeting, 500);
    return;
  }

  showMeeting.value = true;
  nextTick(() => {
    const domain = "meet.jit.si";
    const options = {
      roomName: `GroupMeeting_${props.groupId}`,
      width: "100%",
      height: 500,
      parentNode: document.querySelector("#jitsi-container"),
    };
    const api = new window.JitsiMeetExternalAPI(domain, options);
    jitsiApi.value = api;

    api.addEventListener("videoConferenceJoined", (event) => {
      // removed console.log
    });
    api.addEventListener("participantJoined", (event) => {
      // removed console.log
    });
    api.addEventListener("participantLeft", (event) => {
      // removed console.log
    });
    api.addEventListener("videoConferenceLeft", (event) => {
      // removed console.log
    });
  });
}

watch(
  () => props.currentIndex,
  (newVal) => {
    // removed console.log
  }
);

onMounted(() => {
  const script = document.createElement("script");
  script.src = "https://meet.jit.si/external_api.js";
  script.async = true;
  script.onload = () => {
    console.log("✅ external_api.js 已加载完成");
  };
  script.onerror = () => {
    console.error("❌ external_api.js 加载失败");
  };
  document.body.appendChild(script);
});
</script>

<style scoped>
.task-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: #ffffff;
  width: 100%;
  padding: 1.5rem 2rem; /* updated to provide consistent internal spacing */
  box-sizing: border-box;
  border-radius: 12px;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #111;
}

.task-title {
  margin: 0;
}

.task-info {
  font-size: 1rem;
  color: #666;
  margin-top: -0.5rem;
  margin-bottom: -0.5rem;
}

.task-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.jitsi-container {
  margin-top: 1rem;
  width: 100%;
  height: 500px;
}

.jitsi-container iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}
</style>
