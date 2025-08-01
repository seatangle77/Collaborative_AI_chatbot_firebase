<template>
  <div class="start-meeting-panel">
    <p class="start-title">🚀 讨论即将开始！开始前必须先开启视频录制</p>
    <el-button type="primary" @click="$emit('start-meeting')">
      <VideoCamera style="margin-right: 8px" />
      开始
    </el-button>
  </div>
</template>

<script setup>
import { ElButton } from "element-plus";
import "element-plus/es/components/button/style/css";
import { VideoCamera } from "@element-plus/icons-vue";

// 组件属性已简化，不再需要 jitsiReady
</script>

<style scoped>
.start-meeting-panel {
  width: 100vw;
  max-width: 100vw;
  margin: 0;
  background: #fff;
  border-radius: 0;
  box-shadow: none;
  padding: 0 0 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.start-title {
  font-size: 1.35rem;
  font-weight: 600;
  color: #dc486a;
  margin-bottom: 28px;
  letter-spacing: 0.2px;
  text-align: center;
}

.el-button {
  font-size: 1rem;
  padding: 0.7em 2em;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px 0 rgba(60, 60, 60, 0.06);
  transition: background 0.2s;
}

@media (max-width: 600px) {
  .start-meeting-panel {
    padding: 28px 0 24px 0;
  }
  .start-title {
    font-size: 1.05rem;
    margin-bottom: 16px;
  }
  .el-button {
    font-size: 1rem;
    padding: 0.7em 1.5em;
  }
}
</style>
