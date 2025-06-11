<template>
  <el-card class="speech-panel" header="🎤 实时语音文本">
    <div v-if="speechData.length">
      <ul>
        <li v-for="(entry, index) in speechData" :key="index">
          <strong>{{ entry.user }}:</strong> {{ entry.text }}
        </li>
      </ul>
    </div>
    <div v-else>暂无语音数据</div>
  </el-card>
</template>

<script setup>
defineProps({
  speechData: {
    type: Array,
    default: () => [],
  },
});
</script>

<style scoped>
.speech-panel {
  flex: 1;
  min-height: 300px;
  font-size: 16px;
}
</style>
