<template>
  <el-card class="real-time-stream">
    <h3>实时讨论流</h3>
    <div v-for="message in messages" :key="message.id">
      <el-tag>{{ getUsername(message.user_id) }}:</el-tag>
      <p>{{ message.message }}</p>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  messages: Array,
  users: Object, // user_id -> name 映射
});

// **获取用户名**
const getUsername = (userId) => {
  return props.users?.[userId] || "未知用户";
};
</script>

<style scoped>
.real-time-stream {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
}

h3 {
  font-size: 18px;
  color: #409eff;
}

.el-tag {
  margin-right: 10px;
  background-color: #f4f4f4;
}
</style>
