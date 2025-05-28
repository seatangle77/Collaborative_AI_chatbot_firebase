<template>
  <div class="input-container">
    <!-- ✅ 用户选择 -->
    <el-select
      v-model="selectedUser"
      placeholder="选择用户"
      class="user-select"
      size="large"
    >
      <el-option
        v-for="(user, userId) in users"
        :key="userId"
        :label="user.name"
        :value="userId"
      />
    </el-select>

    <!-- ✅ 消息输入框 -->
    <el-input
      v-model="message"
      placeholder="请输入消息..."
      @input="updateSpeakingDuration"
      @keyup.enter="handleSend"
      class="message-input"
      size="large"
    />

    <!-- ✅ Speaking Duration 输入框 (ms) -->
    <el-input
      v-model="speakingDuration"
      type="number"
      placeholder="时长(ms)"
      class="duration-input"
      size="small"
    />

    <!-- ✅ 发送按钮 -->
    <el-button type="primary" @click="handleSend" size="large" class="send-btn">
      Send
    </el-button>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";

const props = defineProps({
  users: {
    type: Object,
    default: () => ({}),
  },
  groupId: String,
  messages: {
    type: Array,
    default: () => [],
  },
  isTtsPlaying: {
    type: Boolean,
    default: false,
  },
});

const message = ref("");
const selectedUser = ref(null);
const speakingDuration = ref(null); // ✅ 让前端控制 speaking_duration (ms)

onMounted(() => {
  const userIds = Object.keys(props.users);
  if (userIds.length > 0 && !selectedUser.value) {
    selectedUser.value = userIds[0];
  }
});

watch(
  () => props.messages,
  async (newMessages) => {
    const latestMsg = newMessages[newMessages.length - 1];
    const msgId = latestMsg.msgid || latestMsg.msgId; // Use msgId
  }
);

// ✅ **动态计算 speaking_duration（以 ms 计算）**
const updateSpeakingDuration = () => {
  if (message.value.trim()) {
    speakingDuration.value = message.value.length * 50; // 假设 1 字符 ≈ 50ms
  } else {
    speakingDuration.value = null;
  }
};

watch(
  () => props.users,
  (newUsers) => {
    const userIds = Object.keys(newUsers);
    if (userIds.length > 0 && !selectedUser.value) {
      selectedUser.value = userIds[0];
    }
  },
  { immediate: true }
);

const emit = defineEmits(["send-message", "stop-audio-capture"]);

const handleSend = () => {
  if (message.value.trim() && selectedUser.value) {
    emit("send-message", {
      group_id: props.groupId,
      user_id: selectedUser.value,
      message: message.value,
      speaking_duration: speakingDuration.value || null, // ✅ 确保传入毫秒值
    });
    const msgKey = message.value.trim();
    message.value = "";
    speakingDuration.value = null;
  }
};
</script>

<style scoped>
/* ✅ 输入框容器 */
.input-container {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
  box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.05);
  border-radius: 0 0 12px 12px;
}

/* ✅ 用户选择框 */
.user-select {
  width: 140px;
  margin-right: 12px;
}

/* ✅ 消息输入框 */
.message-input {
  flex: 1;
  border-radius: 8px;
  transition: all 0.3s ease-in-out;
}

.message-input:focus-within {
  box-shadow: 0 0 6px rgba(64, 158, 255, 0.6);
}

/* ✅ 时长输入框 */
.duration-input {
  width: 100px;
  margin-left: 8px;
  text-align: center;
  height: 40px;
}

/* ✅ 发送按钮 */
.send-btn {
  padding: 10px 20px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  background: linear-gradient(to right, #409eff, #187bcd);
  transition: all 0.3s ease-in-out;
  margin-left: 12px;
}

.send-btn:hover {
  background: linear-gradient(to right, #5aafff, #1b89e5);
}
</style>
