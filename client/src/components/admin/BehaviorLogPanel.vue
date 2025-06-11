<template>
  <el-card class="behavior-panel" header="🧭 用户行为数据（页面访问/停留）">
    <div v-if="behaviorData.length">
      <ul>
        <li v-for="(event, index) in behaviorData" :key="index">
          <strong>{{ event.user }}:</strong> {{ event.page }} -
          {{ event.duration }}秒
        </li>
      </ul>
    </div>
    <div v-else>暂无行为数据</div>
  </el-card>
</template>

<script setup>
defineProps({
  behaviorData: {
    type: Array,
    default: () => [],
  },
});
</script>

<style scoped>
.behavior-panel {
  flex: 1;
  min-height: 300px;
  font-size: 16px;
}
</style>
