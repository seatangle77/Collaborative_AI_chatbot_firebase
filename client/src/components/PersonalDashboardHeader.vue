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

      <el-button
        type="success"
        class="update-prompt-btn"
        @click="emit('updatePrompt')"
        :disabled="!localUserId"
      >
        Update Prompt
      </el-button>
    </div>

    <div class="header-section header-title">
      <span v-if="localUserId && users[localUserId]">
        {{ users[localUserId].name }}
      </span>
      - {{ selectedSessionTitle || "No Active Session" }}
    </div>

    <span
      class="agent-name"
      @click="emit('toggleDrawer')"
      style="cursor: pointer"
    >
      🤖 {{ agentName }}
      <el-icon style="color: white; margin-left: 5px"><InfoFilled /></el-icon>
    </span>
    <div class="header-section">
      <el-select
        v-model="agentModel"
        class="ai-provider-select"
        @change="handleProviderChange"
      >
        <el-option
          v-for="(label, value) in aiModelOptions"
          :key="value"
          :label="label"
          :value="value"
        />
      </el-select>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";
import { aiModelOptions } from "../utils/constants";
import api from "../services/apiService";
import { ElMessage } from "element-plus";

const props = defineProps({
  groups: Array,
  selectedGroupId: String,
  selectedUser: String,
  agentInfo: Object,
  users: Object,
  filteredUsersInfo: Object,
  selectedSessionTitle: String,
  agentName: String,
  selectedAiProvider: String,
});

const emit = defineEmits([
  "selectGroup",
  "selectUser",
  "updatePrompt",
  "changeAiProvider",
  "toggleDrawer",
]);

const localGroupId = ref(props.selectedGroupId);
const localUserId = ref(props.selectedUser);
const agentModel = ref(props.agentInfo?.model);

watch(
  () => props.selectedGroupId,
  (val) => (localGroupId.value = val)
);
watch(
  () => props.selectedUser,
  (val) => (localUserId.value = val)
);
watch(
  () => props.agentInfo?.model,
  (val) => (agentModel.value = val)
);

const updateModelInDatabase = async (model) => {
  console.log("props.agentInfo.id", props.agentInfo.id);
  if (!props.agentInfo?.id) return;
  try {
    await api.updateAgentModel(props.agentInfo.id, model);
    ElMessage.success("AI 模型已更新");
  } catch (error) {
    console.error("更新模型失败:", error);
    ElMessage.error("更新模型失败");
  }
};

const handleProviderChange = async (newModel) => {
  agentModel.value = newModel;
  await updateModelInDatabase(newModel);
};
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
.user-select,
.ai-provider-select {
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
.update-prompt-btn {
  font-size: 14px;
  padding: 4px 10px;
  font-weight: 500;
  border-radius: 6px;
}
.agent-name {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  margin-right: 4px;
  display: flex;
  align-items: center;
  cursor: pointer;
}
</style>
