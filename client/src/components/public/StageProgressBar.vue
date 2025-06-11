<template>
  <div class="stage-progress-wrapper">
    <div class="stage-info">
      <span class="stage-label">当前阶段：</span>
      <span class="stage-title">阶段 {{ currentStage + 1 }}</span>
    </div>
    <el-progress
      :percentage="progress"
      :stroke-width="6"
      status="success"
      striped
      striped-flow
      :show-text="false"
    />
    <div
      v-if="remainingTime !== null"
      class="countdown-timer"
      :class="{ expired: hasExpired }"
    >
      {{ formatTime(remainingTime) }}<span v-if="hasExpired">（已超时）</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const props = defineProps({
  currentStage: {
    type: Number,
    required: true,
  },
  allocatedTime: {
    type: Number,
    required: true,
  },
});

const progress = ref(0);
const remainingTime = ref(null);
const hasExpired = ref(false);
let intervalId = null;

const formatTime = (seconds) => {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
};

onMounted(() => {
  if (!props.allocatedTime || isNaN(props.allocatedTime)) return;
  const duration = props.allocatedTime * 60;
  let elapsed = 0;
  remainingTime.value = duration;
  intervalId = setInterval(() => {
    elapsed++;
    remainingTime.value = duration - elapsed;
    progress.value = Math.min((elapsed / duration) * 100, 100);
    if (elapsed >= duration) {
      hasExpired.value = true;
    }
  }, 1000);
});

onUnmounted(() => {
  clearInterval(intervalId);
});
</script>

<style scoped>
.stage-progress-wrapper {
  padding: 1.25rem 1.5rem;
  background-color: #ffffff;
  border-radius: 12px;
}

.stage-info {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.stage-label {
  color: #888;
  margin-right: 8px;
}

.stage-title {
  color: #111;
}

.countdown-timer {
  margin-top: 6px;
  font-size: 14px;
  text-align: center;
  color: #555;
}

.expired {
  color: #d93025;
  font-weight: bold;
}
</style>
