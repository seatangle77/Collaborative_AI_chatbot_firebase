<template>
  <el-header class="dashboard-header">
    <div class="header-section">
      <el-select
        v-model="localGroupId"
        class="group-select"
        @change="emit('selectGroup', localGroupId)"
      >
        <el-option
          v-for="group in groups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>

      <el-select
        v-model="localUserId"
        placeholder="选择用户"
        class="user-select"
        @change="emit('selectUser', localUserId)"
      >
        <el-option
          v-for="(user, userId) in filteredUsersInfo"
          :key="userId"
          :label="user.name"
          :value="userId"
        />
      </el-select>
    </div>

    <div class="header-section header-title">
      <span v-if="localUserId && users[localUserId]">
        {{ users[localUserId].name }}
      </span>
      - {{ selectedSessionTitle || "No Active Session" }}
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";

const props = defineProps({
  groups: Array,
  selectedGroupId: String,
  selectedUser: String,
  users: Object,
  filteredUsersInfo: Object,
  selectedSessionTitle: String,
  selectedAiProvider: String,
});

const emit = defineEmits(["selectGroup", "selectUser", "changeAiProvider"]);

const localGroupId = ref(props.selectedGroupId);
const localUserId = ref(props.selectedUser);

watch(
  () => props.selectedGroupId,
  (val) => (localGroupId.value = val)
);
watch(
  () => props.selectedUser,
  (val) => (localUserId.value = val)
);
</script>

<style scoped>
.dashboard-header {
  background-color: #1e90ff;
  color: white;
  padding: 12px 24px;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 1000;
}
.header-section {
  display: flex;
  align-items: center;
  gap: 10px;
}
.group-select,
.user-select {
  width: 200px;
  font-size: 14px;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
}
.header-title {
  flex: 1;
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
