<template>
  <el-popover placement="right" width="260" trigger="click" v-if="userInfo">
    <div class="user-info">
      <img
        v-if="userInfo.avatar_link"
        :src="userInfo.avatar_link"
        class="popover-avatar"
        alt="avatar"
      />
      <p class="name">{{ userInfo.name }}</p>
      <p>
        <strong>🎓 Major:</strong> {{ userInfo.academic_background?.major }}
      </p>
      <p>
        <strong>🔍 Research Focus:</strong>
        {{ userInfo.academic_background?.research_focus }}
      </p>
      <p>
        <strong>🌟 Academic Strengths:</strong>
        {{ userInfo.academic_advantages }}
      </p>
    </div>
    <template #reference>
      <slot />
    </template>
  </el-popover>
</template>

<script setup>
import { onMounted } from "vue";

const props = defineProps({
  userInfo: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped>
.user-info {
  line-height: 1.8;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  color: #1f1f1f;
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  max-width: 260px;
  word-break: break-word;
}

.name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #409eff;
  margin-top: 0px;
}

.popover-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 10px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}
</style>
