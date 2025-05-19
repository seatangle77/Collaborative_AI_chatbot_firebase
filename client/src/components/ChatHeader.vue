<template>
  <el-header class="chat-header">
    <!-- 小组选择器 -->
    <el-select
      v-model="localSelectedGroupId"
      class="group-select"
      popper-class="custom-dropdown"
      @change="emit('selectGroup', localSelectedGroupId)"
    >
      <el-option
        v-for="group in groups"
        :key="group.id"
        :label="group.name"
        :value="group.id"
      />
    </el-select>

    <el-button
      type="success"
      @click="emit('updatePrompt')"
      :disabled="!localSelectedGroupId"
    >
      Update GroupBot Prompt
    </el-button>

    <!-- 会话标题 -->
    <div class="header-title">
      {{ selectedSessionTitle || "No Active Session" }}
    </div>

    <el-button link @click="emit('toggleDrawer')">
      <span v-if="selectedGroupBot" class="bot-name">
        🤖 {{ selectedGroupBot.name }}
      </span>
      <el-icon style="color: white; margin-left: 5px"><InfoFilled /></el-icon>
    </el-button>
    <el-button
      style="position: fixed; top: 100px; right: 20px; z-index: 9999"
      type="primary"
      @click="requestPermissionManually"
    >
      测试通知
    </el-button>

    <!-- AI供应商选择 -->
    <el-select
      v-model="localSelectedAiProvider"
      class="ai-provider-select"
      popper-class="custom-dropdown"
      @change="handleModelChange"
    >
      <el-option
        v-for="(label, value) in aiModelOptions"
        :key="value"
        :label="label"
        :value="value"
      />
    </el-select>
  </el-header>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { InfoFilled } from "@element-plus/icons-vue";
import { aiModelOptions } from "../utils/constants";
import api from "../services/apiService";

const props = defineProps({
  groups: Array,
  selectedGroupId: String,
  selectedAiProvider: String,
  selectedGroupBot: Object,
  selectedSessionTitle: String,
});

const emit = defineEmits([
  "selectGroup",
  "changeAiProvider",
  "updatePrompt",
  "toggleDrawer",
]);

const localSelectedGroupId = ref(props.selectedGroupId);
const localSelectedAiProvider = ref(props.selectedAiProvider);

onMounted(() => {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/service-worker.js")
      .then(() => {
        console.log("✅ Service Worker 注册成功");
      })
      .catch((err) => {
        console.error("❌ Service Worker 注册失败:", err);
      });
  }
});

const requestPermissionManually = () => {
  if ("Notification" in window && "serviceWorker" in navigator) {
    console.log("🧪 Notification supported");

    Notification.requestPermission()
      .then((permission) => {
        console.log("🔐 权限状态：", permission);
        if (permission === "granted") {
          navigator.serviceWorker.getRegistration().then((reg) => {
            if (reg) {
              reg.showNotification("🔔心率变异性（HRV)", {
                body: "指逐次心跳周期时间长度的微小波动",
              });
              ElMessage.success("✅ 系统通知已发送，请检查通知栏");
            } else {
              ElMessage.error("❌ 无法获取 Service Worker 实例");
            }
          });
        } else {
          console.warn("❌ 用户拒绝了通知权限");
          ElMessage.warning("用户未授权通知，无法发送提醒");
        }
      })
      .catch((err) => {
        console.error("❌ Notification.requestPermission 失败:", err);
        ElMessage.error("请求通知权限失败：" + err.message);
      });
  } else {
    console.warn("❌ 当前浏览器不支持 Notification 或 Service Worker");
    ElMessage.error("当前浏览器不支持系统通知");
  }
};

const handleModelChange = async (newModel) => {
  if (props.selectedGroupBot?.id) {
    try {
      await api.updateBotModel(props.selectedGroupBot.id, newModel);
      ElMessage.success("AI 模型已更新！");
    } catch (error) {
      console.error("更新 AI 模型失败:", error);
    }
  }
  emit("changeAiProvider", newModel);
};

watch(
  () => props.selectedGroupId,
  (val) => {
    localSelectedGroupId.value = val;
  }
);
watch(
  () => props.selectedAiProvider,
  (val) => {
    localSelectedAiProvider.value = val;
  }
);
watch(
  () => props.selectedGroupBot,
  (newBot) => {
    if (newBot?.model) {
      localSelectedAiProvider.value = newBot.model;
      emit("changeAiProvider", newBot.model);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.chat-header {
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
.group-select,
.ai-provider-select {
  width: 200px;
  font-size: 14px;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
}
.el-button {
  font-weight: 500;
  border-radius: 6px;
}
.header-title {
  flex: 1;
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
.bot-name {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  margin-right: 4px;
}
</style>
