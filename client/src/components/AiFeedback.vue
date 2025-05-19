<template>
  <div class="ai-feedback">
    <el-tooltip
      content="Was this AI-generated content helpful?"
      placement="top"
    >
      <el-button-group>
        <el-button
          size="small"
          @click="handleFeedback('like')"
          :type="currentFeedback.like ? 'primary' : 'default'"
          :class="{ 'selected-like': currentFeedback.like }"
          >👍</el-button
        >
        <el-button
          size="small"
          @click="handleFeedback('dislike')"
          :type="currentFeedback.dislike ? 'danger' : 'default'"
          :class="{ 'selected-dislike': currentFeedback.dislike }"
          >👎</el-button
        >
        <el-button size="small" @click="toggleComment">💬</el-button>
      </el-button-group>
    </el-tooltip>

    <div v-if="showComment" class="comment-box">
      <el-input
        v-model="comment"
        placeholder="Leave your comment here"
        @keyup.enter="submitComment"
        size="small"
      />
      <el-button size="small" @click="submitComment">Submit</el-button>
    </div>

    <div
      v-if="currentFeedback.like || currentFeedback.dislike"
      class="feedback-status"
    >
      You rated this as:
      <span v-if="currentFeedback.like" class="like-text">👍 Helpful</span>
      <span v-if="currentFeedback.dislike" class="dislike-text"
        >👎 Not helpful</span
      >
    </div>

    <div v-if="currentFeedback.comment_text" class="feedback-status">
      💬 Your comment:
      <span class="comment-text">{{ currentFeedback.comment_text }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
import api from "../services/apiService";
import { ElMessage } from "element-plus";

const props = defineProps({
  summaryId: String,
  messageId: String,
  groupId: String,
  botId: String,
  model: String,
  sessionId: String,
  userId: String,
  promptType: String,
  promptVersion: String,
  targetId: String,
});

const targetId = props.targetId;

const isReady = computed(() => {
  return (
    props.targetId &&
    props.groupId &&
    props.botId &&
    props.model &&
    props.sessionId &&
    props.userId &&
    props.promptType &&
    props.promptVersion
  );
});

const showComment = ref(false);
const comment = ref("");
const currentFeedback = ref({
  like: false,
  dislike: false,
  comment_text: "",
});

const fetchLatestFeedback = async (skipIfEmpty = false) => {
  try {
    const response = await api.getBotFeedback({
      user_id: props.userId,
      bot_id: props.botId,
      target_id: props.targetId,
      prompt_type: props.promptType,
    });

    if (response) {
      const feedback = response;
      currentFeedback.value = {
        like: feedback.like,
        dislike: feedback.dislike,
        comment_text: feedback.comment_text || "",
      };
      comment.value = feedback.comment_text || "";
    } else {
      // Only clear if skipIfEmpty is explicitly false
      if (!skipIfEmpty) {
        currentFeedback.value = {
          like: false,
          dislike: false,
          comment_text: "",
        };
        comment.value = "";
      }
    }
  } catch (error) {
    console.error("❌ Failed to fetch latest feedback:", error);
  }
};

watch(
  () => ({ ...props }),
  (newProps) => {},
  { deep: true, immediate: true }
);

watch(
  () => ({
    targetId: props.targetId,
    userId: props.userId,
    botId: props.botId,
    groupId: props.groupId,
    promptType: props.promptType,
    promptVersion: props.promptVersion,
  }),
  (newProps) => {
    if (
      newProps.targetId &&
      newProps.userId &&
      newProps.botId &&
      newProps.groupId &&
      newProps.promptType &&
      newProps.promptVersion
    ) {
      fetchLatestFeedback();
    }
  },
  { immediate: true, deep: true }
);

watch(
  () => props.targetId,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      console.log("📌 targetId changed:", oldVal, "→", newVal);
      fetchLatestFeedback();
    }
  }
);

watch(
  () => props.targetId,
  (newVal, oldVal) => {
    console.log("🔁 AiFeedback targetId updated:", oldVal, "→", newVal);
  }
);

watch(
  isReady,
  (ready) => {
    if (ready) {
      fetchLatestFeedback();
    }
  },
  { immediate: true }
);

onMounted(() => {
  console.log("🧩 AiFeedback mounted with props:", {
    targetId: props.targetId,
    botId: props.botId,
    sessionId: props.sessionId,
    userId: props.userId,
    promptType: props.promptType,
    promptVersion: props.promptVersion,
  });
  fetchLatestFeedback();
});

const toggleComment = () => {
  showComment.value = !showComment.value;
};

const handleFeedback = async (type) => {
  try {
    const isCancelling = currentFeedback.value[type];
    await api.submitBotFeedback({
      prompt_type: props.promptType,
      group_id: props.groupId,
      bot_id: props.botId,
      ai_model: props.model,
      session_id: props.sessionId,
      user_id: props.userId,
      like: type === "like" ? !isCancelling : currentFeedback.value.like,
      dislike:
        type === "dislike" ? !isCancelling : currentFeedback.value.dislike,
      comment_text: currentFeedback.value.comment_text,
      prompt_version: props.promptVersion,
      target_id: props.targetId,
    });

    currentFeedback.value.like =
      type === "like" ? !isCancelling : currentFeedback.value.like;
    currentFeedback.value.dislike =
      type === "dislike" ? !isCancelling : currentFeedback.value.dislike;

    ElMessage.success(
      isCancelling ? "Feedback canceled" : "Feedback submitted"
    );

    setTimeout(() => {
      fetchLatestFeedback(true);
    }, 300);
  } catch (error) {
    console.error("Failed to submit feedback:", error);
    ElMessage.error("Failed to submit feedback");
  }
};

const submitComment = async () => {
  if (!comment.value.trim()) return;
  try {
    await api.submitBotFeedback({
      prompt_type: props.promptType,
      group_id: props.groupId,
      bot_id: props.botId,
      ai_model: props.model,
      session_id: props.sessionId,
      user_id: props.userId,
      like: currentFeedback.value.like,
      dislike: currentFeedback.value.dislike,
      comment_text: comment.value,
      prompt_version: props.promptVersion,
      target_id: props.targetId,
    });

    ElMessage.success("Comment submitted");

    currentFeedback.value.comment_text = comment.value;
    showComment.value = false;

    setTimeout(() => {
      fetchLatestFeedback(true);
    }, 300);
  } catch (error) {
    console.error("Failed to submit comment:", error);
  }
};
</script>

<style scoped>
.ai-feedback {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica,
    Arial, sans-serif;
}

.el-button-group {
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.el-button {
  border: none;
  background-color: transparent;
  font-size: 16px;
  padding: 6px 12px;
  transition: background-color 0.2s ease;
}

.el-button:hover {
  background-color: #f0f0f5;
}

.comment-box {
  margin-top: 10px;
  width: 100%;
}

.comment-box .el-input {
  width: 100%;
  margin-bottom: 6px;
}

.comment-box .el-button {
  background-color: #007aff;
  color: white;
  font-weight: 500;
  border-radius: 6px;
  font-size: 12px;
  padding: 4px 10px;
}

.comment-box .el-button:hover {
  background-color: #005ecb;
}

.selected-like {
  background-color: #e6f4ea;
  color: #219653;
}

.selected-dislike {
  background-color: #ffe6e6;
  color: #ff4d4f;
}

.feedback-status {
  margin-top: 6px;
  font-size: 13px;
  font-style: italic;
}

.feedback-status .like-text {
  color: #219653;
  font-weight: 500;
}

.feedback-status .dislike-text {
  color: #ff4d4f;
  font-weight: 500;
}
</style>
