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
        :status="mapStatus(item.status)"
      />
    </el-steps>
    <p v-if="showSteps && agendaItems.length === 0" class="empty-warning">
      ⚠️ 当前无可用议程，请检查数据加载状态。
    </p>
  </div>
</template>

<script setup>
import { CaretRight, RefreshLeft } from "@element-plus/icons-vue";
import { ref, watchEffect, watch } from "vue";

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

const showSteps = ref(true);
const internalIndex = ref(props.currentIndex);
const unlockedStepIndex = ref(0);

const mapStatus = (status) => {
  if (status === "in_progress") return "process";
  if (status === "completed") return "finish";
  return "wait";
};

watchEffect(() => {
  emit("update:currentIndex", internalIndex.value);
});

watchEffect(() => {
  console.log("📊 agendaItems in StageTimeline:", props.agendaItems);
});

watch(
  () => props.agendaItems,
  (newVal) => {
    console.log("📍 agendaItems changed:", newVal);
    if (newVal.length > 0) {
      showSteps.value = true;
    }
  },
  { immediate: true, deep: true }
);
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

.empty-warning {
  color: #f56c6c;
  font-weight: 600;
  margin-top: 1rem;
}
</style>
