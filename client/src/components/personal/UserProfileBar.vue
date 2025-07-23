<template>
  <div class="user-overview">
    <div class="user-overview-bar">
      <div class="top-row">
        <div style="display: flex; flex-direction: column">
          <div class="left-info">
            <el-select
              v-model="localSelectedUserId"
              class="user-select"
              size="small"
              @change="handleUserChange"
              placeholder="请选择用户"
              style="display: none"
            >
              <el-option
                v-for="u in allUsers"
                :key="u.user_id"
                :label="u.name"
                :value="u.user_id"
              />
            </el-select>
            <span class="group" v-if="group?.name">{{ group.name }}</span>
          </div>
        </div>
        <div class="right-info">
          <el-space>
            <el-tag
              v-for="m in members"
              :key="m.user_id"
              size="small"
              type="success"
              round
            >
              {{ displayMemberName(m) }}
            </el-tag>
            <el-tooltip
              content="模型：{{ bot.model }}"
              placement="top"
              v-if="bot?.model"
            >
              <el-tag
                size="small"
                type="info"
                @click="showModelDialog = true"
                style="cursor: pointer"
              >
                🤖 {{ bot.name }}
              </el-tag>
            </el-tooltip>
          </el-space>
        </div>
      </div>
    </div>
    <el-dialog v-model="showModelDialog" title="选择 AI 模型" width="300px">
      <p>当前模型：{{ bot.model }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";

const props = defineProps({
  bot: Object,
  allUsers: Array,
  selectedUserId: String,
  members: Array,
  group: Object,
  session: Object, // added session prop to access session_title and session_date
  routeName: String, // 新增
});

const emit = defineEmits(["update:selectedUserId"]);

const handleUserChange = (newId) => {
  emit("update:selectedUserId", newId);
};

// 双向绑定 selectedUserId，初始化时给它一个默认值
const localSelectedUserId = ref("");

// 初始化时设置一次
if (!localSelectedUserId.value && props.selectedUserId) {
  localSelectedUserId.value = props.selectedUserId;
}

// 监听 selectedUserId prop 变化
watch(
  () => props.selectedUserId,
  (val) => {
    localSelectedUserId.value = val;
  }
);

// 监听 routeName 和 allUsers，自动匹配 user
watch(
  [() => props.routeName, () => props.allUsers],
  ([newRouteName, newAllUsers]) => {
    if (newRouteName && Array.isArray(newAllUsers)) {
      const match = newAllUsers.find(u => u.name === newRouteName);
      if (match) {
        localSelectedUserId.value = match.user_id;
        handleUserChange(match.user_id); // 触发用户切换
      }
    }
  },
  { immediate: true }
);

const showModelDialog = ref(false);

const sessionTitle = computed(
  () => props.session?.session_title || "未命名议题"
);

// Watch for changes in members prop and log updates
watch(
  () => props.members,
  (newMembers) => {
    console.log("🔁 members updated:", newMembers);
  },
  { immediate: true, deep: true }
);

const displayMemberName = (m) => {
  return m.name;
};
</script>

<style scoped>
.user-overview {
  width: 100%;
}
.user-overview-bar {
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.5rem 0.5rem 0.5rem;
  font-size: 14px;
  background-color: #ffffff;
  border-radius: 12px;
  box-sizing: border-box;
  font-family: "Helvetica Neue", Arial, sans-serif;
}

.top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  width: 100%;
}

.session-row {
  width: 100%;
  text-align: center;
  margin-top: 4px;
}

.session-name {
  font-size: 18px;
  font-weight: 500;
  color: #555;
}

.left-info {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 1rem;
  min-height: 32px;
}

.right-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.right-info > .el-tag:last-child {
  margin-left: 0.5rem;
}

.group,
.user-select {
  font-size: 14px;
  color: #606266;
}

.user-select {
  width: 160px;
  margin-bottom: 0;
}
.member-row {
  margin-top: 1rem;
  width: 100%;
}

.session-detail {
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-top: 2px;
}
</style>
