<template>
  <el-card class="summary-panel">
    <div class="summary-header">
      <span class="summary-title">✨ AI Real-Time Summary</span>
      <el-tag
        type="info"
        class="summary-status"
        v-if="!parsedSummary && !errorText"
      >
        Processing...
      </el-tag>
    </div>

    <!-- 🔹 AI 处理中 / 错误展示 -->
    <p v-if="errorText" class="error-text">⚠️ {{ errorText }}</p>
    <p v-if="isLoading && !parsedSummary && !errorText" class="loading-text">
      AI is analyzing the discussion...
    </p>

    <!-- 🔹 展示最新 AI 总结 -->
    <div v-if="parsedSummary">
      <p><strong>🔹 Topic: </strong> {{ parsedSummary.current_topic }}</p>

      <p><strong>📌 Key Points:</strong></p>
      <ul class="summary-list">
        <li
          v-for="(point, index) in parsedSummary.key_points"
          :key="'point-' + index"
        >
          {{ point }}
        </li>
      </ul>

      <p><strong>💡 Suggestions:</strong></p>
      <ul class="summary-list">
        <li
          v-for="(suggestion, index) in parsedSummary.suggestions"
          :key="'suggestion-' + index"
        >
          {{ suggestion }}
        </li>
      </ul>

      <p v-if="parsedSummary.unresolved_issues.length > 0">
        <strong>❓ Unresolved Issues: </strong>
      </p>
      <ul class="summary-list">
        <li
          v-for="(issue, index) in parsedSummary.unresolved_issues"
          :key="'issue-' + index"
        >
          {{ issue }}
        </li>
      </ul>
      <ai-feedback
        :key="feedbackKey"
        :group-id="groupId"
        :session-id="sessionId"
        :bot-id="botId"
        :user-id="userId"
        :model="currentBotModel"
        :prompt-type="promptType"
        :prompt-version="promptVersion"
        :target-id="latestSummaryId"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
import api from "../services/apiService";
import AiFeedback from "./AiFeedback.vue";

const props = defineProps({
  discussion_summary: Array,
  groupId: String,
  sessionId: String,
  botId: String,
  userId: String,
  model: String,
  promptType: String,
  promptVersion: String,
  usersInfo: Object,
  selectedGroupBot: Object,
  aiBots: Array,
});

const parsedSummary = ref(null);
const errorText = ref("");
const isLoading = ref(false); // 新增状态变量
const feedbackKey = ref(Date.now());
const latestSummaryId = ref(null); // Changed from computed to ref

const currentBotModel = computed(() => props.selectedGroupBot?.model || "");

// ✅ **解析 AI 会议总结**
const parseAiSummary = (insightText) => {
  if (
    typeof insightText !== "string" ||
    insightText.includes("AI 生成失败") ||
    insightText.includes("未知的 AI 提供商") ||
    insightText.includes("Server not responding")
  ) {
    errorText.value = insightText;
    parsedSummary.value = null;
    return;
  }

  try {
    let cleanedText = insightText.trim();

    if (cleanedText.startsWith("❌ AI 生成失败")) {
      parsedSummary.value = null;
      return;
    }

    // 🔹 去掉 ```json 包裹
    if (cleanedText.startsWith("```json")) {
      cleanedText = cleanedText.replace(/^```json\n/, "").replace(/\n```$/, "");
    }

    // 新增：去掉 JSON string 包裹字符
    if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
      cleanedText = cleanedText.slice(1, -1);
    }

    // ✅ 新增：去掉转义斜杠
    cleanedText = cleanedText.replace(/\\"/g, '"');

    const parsedJson = JSON.parse(cleanedText);

    if (parsedJson.summary) {
      parsedSummary.value = {
        current_topic: parsedJson.summary.current_topic || "No topic found",
        key_points: parsedJson.summary.key_points || [],
        suggestions: parsedJson.summary.suggestions || [],
        unresolved_issues: parsedJson.summary.unresolved_issues || [],
      };
      errorText.value = "";
    } else {
      console.warn("⚠️ AI summary format incorrect:", parsedJson);
    }
  } catch (error) {
    console.error("❌ Failed to parse AI JSON response:", error);
    parsedSummary.value = null;
  }
};

// ✅ **RESTful API 获取最新 AI Summary**
const fetchLatestSummary = async (groupId) => {
  if (!groupId) return;
  isLoading.value = true; // 开始加载时设置为 true
  try {
    const summaries = await api.fetchLatestSummary(groupId);
    if (summaries.length > 0) {
      const latestSummary = summaries[0];
      latestSummaryId.value = latestSummary.id;
      feedbackKey.value = latestSummary.id;
      const summaryText = latestSummary.summary_text;
      if (typeof summaryText === "string") {
        parseAiSummary(summaryText);
      } else {
        console.warn("⚠️ summary_text is not a string:", summaryText);
        parsedSummary.value = null;
      }
    }
  } catch (error) {
    console.error("❌ Failed to fetch AI summary:", error);
  } finally {
    isLoading.value = false; // 结束时设置为 false
  }
};

const fetchLatestSummaryId = async (groupId) => {
  if (!groupId) return;
  try {
    const summaries = await api.fetchLatestSummary(groupId);
    if (summaries.length > 0) {
      const latestSummary = summaries[0];
      if (latestSummary?.id) {
        feedbackKey.value = latestSummary.id;
        latestSummaryId.value = latestSummary.id; // Added this line
        parsedSummary.value = { ...parsedSummary.value }; // Force re-evaluation of the DOM
      }
    }
  } catch (error) {
    console.error("❌ Failed to fetch latest summary ID:", error);
  }
};

// ✅ **监听 WebSocket 或 API 更新**
watch(
  () => props.discussion_summary,
  (newSummary) => {
    if (!newSummary || newSummary.length === 0) {
      parsedSummary.value = null;
      return;
    }

    try {
      let latestSummary = newSummary[newSummary.length - 1];

      // 🔹 处理 REST API 或 WebSocket 的数据格式
      if (Array.isArray(latestSummary)) {
        latestSummary = latestSummary[0];
      }

      if (!latestSummary || !latestSummary.summary_text) {
        parsedSummary.value = null;
        return;
      }

      const summaryText = latestSummary.summary_text;
      if (typeof summaryText === "string") {
        parseAiSummary(summaryText);
        feedbackKey.value = Date.now();
      } else {
        parsedSummary.value = null;
      }
    } catch (error) {
      console.error("❌ Failed to parse AI JSON response:", error);
      parsedSummary.value = null;
    }
  },
  { deep: true, immediate: true }
);

// 替换复合 watch 语句
watch(
  () => props.discussion_summary,
  (newSummary) => {
    if (
      Array.isArray(newSummary) &&
      newSummary.length > 0 &&
      typeof newSummary.at(-1)?.summary_text === "string"
    ) {
      fetchLatestSummaryId(props.groupId);
    }
  },
  { deep: true, immediate: true }
);

// ✅ **组件初始化时加载最新 AI Summary**
onMounted(() => {
  fetchLatestSummary(props.groupId);
});
</script>

<style scoped>
/* 🔹 主体容器 */
.summary-panel {
  width: 100%;
  height: 100%;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* 🔹 头部 */
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 🔹 AI 处理中 */
.loading-text {
  font-size: 14px;
  color: #aaa;
  text-align: center;
  padding: 10px 0;
}

/* 🔹 错误文本 */
.error-text {
  color: #e53935;
  font-size: 14px;
  text-align: center;
  padding: 10px 0;
}

/* 🔹 AI 总结列表 */
.summary-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 20px;
}

.summary-list li {
  list-style-type: disc;
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}
</style>
