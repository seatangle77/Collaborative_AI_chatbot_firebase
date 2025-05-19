<template>
  <el-card class="terminology-helper">
    <h3>跨学科知识库</h3>
    <el-skeleton v-if="loading" animated />
    <el-empty
      v-else-if="terms.length === 1 && terms[0].term === '暂无术语'"
      description="当前尚无术语解释记录，请先进行术语查询。"
    />
    <el-collapse v-else>
      <el-collapse-item
        v-for="(term, index) in terms"
        :key="index"
        :name="term.term_name"
      >
        <template #title>{{ term.term_name }}</template>
        <h4 v-if="term.definition">📖 术语定义</h4>
        <p v-if="term.definition">{{ term.definition }}</p>
        <h4 v-if="Array.isArray(term.cross_discipline_insights)">
          🔍 跨学科洞见
        </h4>
        <ul v-if="Array.isArray(term.cross_discipline_insights)">
          <li v-for="(item, i) in term.cross_discipline_insights" :key="i">
            {{ item }}
          </li>
        </ul>
        <h4 v-if="Array.isArray(term.application_examples)">💡 应用示例</h4>
        <ul v-if="Array.isArray(term.application_examples)">
          <li v-for="(example, i) in term.application_examples" :key="i">
            {{ example }}
          </li>
        </ul>
        <div class="ai-feedback-wrapper" style="margin-top: 12px">
          <AgentFeedback
            v-if="agentId && term.insight_id"
            :agentId="agentId"
            :targetId="term.insight_id"
            :aiModel="props.agentModel"
            promptType="terminology_explanation"
            :promptVersion="promptVersion_term_explanation"
          />
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>
<script setup>
import { ref, defineProps, onMounted, watch } from "vue";
import apiService from "../services/apiService";
import AgentFeedback from "../components/AgentFeedback.vue";

const props = defineProps({
  groupId: {
    type: [String, null],
    required: false,
  },
  agentId: {
    type: [String, null],
    required: false,
  },
  insightsResponse: {
    type: Function,
    required: false,
  },
  refreshSignal: {
    type: [Number, String],
    required: false,
  },
  agentModel: {
    type: String,
    required: false,
  },
  promptVersion_term_explanation: {
    type: String,
    required: false,
  },
});

const terms = ref([]);
const loading = ref(true);

const fetchTerm = async () => {
  const insights = await apiService.getDiscussionInsightsByGroupAndAgent(
    props.groupId,
    props.agentId
  );
  if (insights) {
    const parsedTerms = insights.map((insight) => {
      const rawText = insight.insight_text.trim();
      const cleanText = rawText.startsWith("```json")
        ? rawText
            .replace(/^```json/, "")
            .replace(/```$/, "")
            .trim()
        : rawText;
      try {
        const parsed = JSON.parse(cleanText);
        return {
          term_name: insight.term_name || "未命名术语",
          insight_id: insight.insight_id,
          ...parsed.term_explanation,
        };
      } catch (e) {
        console.error("JSON parse error:", e);
        return {
          term_name: "解析失败",
          definition: "无法解析术语解释。",
          cross_discipline_insights: [],
          application_examples: [],
        };
      }
    });

    if (props.insightsResponse) {
      props.insightsResponse(insights);
    } else {
      terms.value = parsedTerms;

      if (terms.value.length === 0) {
        terms.value = [
          {
            term: "暂无术语",
            definition: "当前尚无术语解释记录，请尝试先进行术语查询。",
            cross_discipline_insights: [],
            application_examples: [],
          },
        ];
      }
    }
  }
  loading.value = false;
};

onMounted(() => {
  if (props.groupId && props.agentId) {
    fetchTerm();
  }
});

watch(
  [() => props.groupId, () => props.agentId],
  ([newGroupId, newAgentId]) => {
    if (newGroupId && newAgentId) {
      fetchTerm();
    }
  }
);

watch(
  () => props.refreshSignal,
  () => {
    if (props.groupId && props.agentId) {
      console.log("🔁 检测到 refreshSignal 变更，重新拉取术语");
      fetchTerm();
    }
  }
);

watch(
  () => props.agentModel,
  (newVal, oldVal) => {
    console.log("🧠 agentModel 变更:", oldVal, "➡", newVal);
  }
);
</script>
<style scoped>
.terminology-helper h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1f2d3d;
}

.terminology-helper :deep(.el-collapse-item__header) {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  padding: 12px 20px;
}

.terminology-helper p,
.terminology-helper li {
  font-size: 14px;
}

.terminology-helper p {
  color: #4a4a4a;
  line-height: 1.6;
  margin-bottom: 10px;
}

.terminology-helper h4 {
  color: #409eff;
  margin: 14px 0 6px;
  font-size: 14px;
  font-weight: 500;
}

.terminology-helper ul {
  padding-left: 20px;
  margin-bottom: 12px;
}

.terminology-helper li {
  margin-bottom: 6px;
  line-height: 1.5;
  color: #333;
}

.terminology-helper .el-collapse-item__content {
  padding: 10px 20px;
}
</style>
