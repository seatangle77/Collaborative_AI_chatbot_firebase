<template>
  <div v-if="showSteps" class="agenda-timeline">
    <el-steps
      :active="internalIndex"
      align-center
      :space="'25%'"
      process-status="process"
    >
      <el-step
        v-for="(item, index) in agendaItems"
        :key="index"
        :title="item.agenda_title"
        class="step-item"
        :disabled="index > unlockedStepIndex"
        @click="handleStepClick(index)"
      />
    </el-steps>
  </div>
  <div v-if="!showSteps" class="start-button-container">
    <el-button
      class="agenda-button"
      type="primary"
      @click="startAgenda"
      size="small"
    >
      <el-icon><CaretRight /></el-icon>
    </el-button>
  </div>
  <div v-if="showSteps" class="restart-button-container">
    <el-button
      class="agenda-button"
      type="default"
      @click="restartAgenda"
      size="small"
    >
      <el-icon><RefreshLeft /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { CaretRight, RefreshLeft } from "@element-plus/icons-vue";
import { ref, watchEffect } from "vue";
import api from "../../services/apiService";
import { ElMessage } from "element-plus";

const emit = defineEmits(["update:currentIndex", "selectStage"]);
const props = defineProps({
  agendaItems: {
    type: Array,
    required: true,
  },
  currentIndex: {
    type: Number,
    default: -1,
  },
  sessionId: {
    type: String,
    default: null,
  },
  groupId: {
    type: String,
    required: true,
  },
});

const showSteps = ref(false);
const internalIndex = ref(props.currentIndex);
const unlockedStepIndex = ref(0);

watchEffect(() => {
  emit("update:currentIndex", internalIndex.value);
});

async function handleStepClick(index) {
  if (index <= unlockedStepIndex.value) {
    internalIndex.value = index;
    emit("selectStage", index);

    await api.resetAgendaStatus(props.groupId, index + 1); // 下一步状态为进行中
    ElMessage.success(`已进入第 ${index + 1} 步`);
    if (
      index === unlockedStepIndex.value &&
      index < props.agendaItems.length - 1
    ) {
      unlockedStepIndex.value++;
    }
  }
}

async function startAgenda() {
  await api.resetAgendaStatus(props.groupId, 0);
  ElMessage.success("议程已开始");
  showSteps.value = true;
  internalIndex.value = -1;
  unlockedStepIndex.value = 0;
}

async function restartAgenda() {
  await api.resetAgendaStatus(props.groupId, 0);
  ElMessage.success("议程已重置");
  internalIndex.value = -1;
  showSteps.value = false;
  unlockedStepIndex.value = 0;
}
</script>

<style scoped>
.agenda-timeline {
  padding: 1rem 0;
  background: #fff;
  text-align: center;
  width: 100%;
  margin: 0 auto;
  border-radius: 12px;
}

.agenda-header {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 18px;
  color: #1f2d3d;
  justify-content: center;
  margin-bottom: 1rem;
}

::v-deep(.el-steps) {
  justify-content: center;
}

::v-deep(.el-step__title) {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: normal;
  line-height: 1.4;
}

::v-deep(.step-item) {
  cursor: pointer;
}

::v-deep(.el-step__title:hover) {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}

.start-button-container,
.restart-button-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.agenda-button {
  padding: 15px 20px;
  font-size: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
}

.start-button-container .el-icon,
.restart-button-container .el-icon {
  font-size: 20px;
}
</style>
