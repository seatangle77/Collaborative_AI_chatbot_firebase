<template>
  <div class="cognitive-feedback">
    <el-card class="box-card" v-if="!hasError">
      <template #header>
        <div class="card-header">
          <span>🧠 认知分析报告</span>
        </div>
      </template>
      <div class="ai-section" v-if="cognitiveData">
        <p><strong>成员认知水平：</strong></p>
        <ul>
          <li
            v-for="(level, member) in cognitiveData.member_levels"
            :key="member"
          >
            {{ member }}：{{ level }}
          </li>
        </ul>
        <p>
          <strong>小组平均水平：</strong>
          {{ cognitiveData.group_average_level }}
        </p>
        <p>
          <strong>认知偏好：</strong> {{ cognitiveData.group_cognitive_bias }}
        </p>
        <p><strong>总结：</strong></p>
        <p style="white-space: pre-line">{{ cognitiveData.summary }}</p>
      </div>
    </el-card>
    <el-divider />

    <el-card class="box-card" v-if="!hasError" style="margin-top: 12px">
      <template #header>
        <div class="card-header">
          <span>📊 行为参与分析</span>
        </div>
      </template>
      <div class="ai-section" v-if="behaviorData">
        <p><strong>成员活跃度等级：</strong></p>
        <ul>
          <li
            v-for="(level, member) in behaviorData.member_levels"
            :key="member"
          >
            {{ member }}：{{ level }}
          </li>
        </ul>
        <p><strong>行为指标：</strong></p>
        <ul>
          <li>
            发言次数平均：{{
              behaviorData.behavior_metrics.average_speech_count
            }}
          </li>
          <li>编辑次数：{{ behaviorData.behavior_metrics.edit_count }}</li>
          <li>点击事件数：{{ behaviorData.behavior_metrics.click_events }}</li>
        </ul>
        <p><strong>总结：</strong></p>
        <p style="white-space: pre-line">
          {{ behaviorData.group_behavior_summary }}
        </p>
      </div>
    </el-card>
    <el-divider />

    <el-card class="box-card" v-if="!hasError" style="margin-top: 12px">
      <template #header>
        <div class="card-header">
          <span>🎯 注意力分析</span>
        </div>
      </template>
      <div class="ai-section" v-if="attentionData">
        <p><strong>成员注意力状态：</strong></p>
        <ul>
          <li
            v-for="(state, member) in attentionData.shared_attention_score"
            :key="member"
          >
            {{ member }}：{{ state }}
          </li>
        </ul>
        <p>
          <strong>小组注意力状态：</strong>
          {{ attentionData.group_attention_n_state }}
        </p>
        <p><strong>分析说明：</strong></p>
        <p style="white-space: pre-line">
          {{ attentionData.attention_explanation }}
        </p>
        <p><strong>建议：</strong></p>
        <p style="white-space: pre-line">{{ attentionData.suggestion }}</p>
      </div>
    </el-card>
    <el-alert
      v-else
      type="error"
      title="AI 分析解析失败"
      description="请检查后端返回内容格式是否正确。"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  aiSummary: {
    type: Object,
    required: false,
  },
  feedbackData: {
    type: Object,
    required: false,
  },
});
import { computed } from "vue";
import { marked } from "marked";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

// 配置 marked 使用 highlight.js 进行代码高亮
marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
});

// 提取并格式化 markdown 中的 ```json ... ``` 内容，仅返回格式化后的 JSON 对象
const extractAndFormatJson = (raw) => {
  if (!raw || typeof raw !== "string") return null; // 防止 match 报错
  const jsonMatch = raw.match(/```json\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    try {
      const cleaned = jsonMatch[1]
        .replace(/\\n/g, "\\n") // keep escaped line breaks
        .replace(/\\+"/g, '"') // unescape quotes if needed
        .replace(/\r/g, "") // remove carriage returns
        .replace(/[\x00-\x1F]+/g, " "); // remove bad control characters
      return JSON.parse(cleaned);
    } catch (e) {
      console.error("JSON parse error", e);
    }
  }
  return null;
};

const cognitiveData = computed(() =>
  extractAndFormatJson(
    props.aiSummary?.cognitive?.raw_response ||
      props.feedbackData?.cognitive?.raw_response
  )
);
const behaviorData = computed(() =>
  extractAndFormatJson(
    props.aiSummary?.behavior?.raw_response ||
      props.feedbackData?.behavior?.raw_response
  )
);
const attentionData = computed(() =>
  extractAndFormatJson(
    props.aiSummary?.attention?.raw_response ||
      props.feedbackData?.attention?.raw_response
  )
);

const hasError = computed(
  () =>
    props.aiSummary?.cognitive?.error ||
    props.aiSummary?.behavior?.error ||
    props.aiSummary?.attention?.error ||
    props.feedbackData?.cognitive?.error ||
    props.feedbackData?.behavior?.error ||
    props.feedbackData?.attention?.error
);
</script>

<style scoped>
.cognitive-feedback {
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
}
.ai-section {
  padding: 16px;
  white-space: pre-wrap;
  line-height: 1.6;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #444;
}
.card-header {
  font-weight: bold;
  font-size: 16px;
  color: #2c3e50;
}

pre code {
  display: block;
  overflow-x: auto;
  padding: 1em;
  background: #f6f8fa;
  color: #24292e;
  border-radius: 4px;
  font-size: 13px;
}
</style>
