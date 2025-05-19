<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="(val) => emit('update:visible', val)"
    title="🤖 AI Bot Details"
    size="70%"
    direction="ltr"
    :with-header="true"
  >
    <div v-if="bot">
      <h3>{{ bot.name }}</h3>
      <p style="margin-bottom: 10px">
        {{ bot.description || "No description available." }}
      </p>

      <el-tabs
        v-model="activeTab"
        class="version-tabs"
        style="margin-top: 20px"
      >
        <el-tab-pane label="🧭 Cognitive Guidance" name="cognitive_guidance" />
        <el-tab-pane label="📄 Real-Time Summary" name="real_time_summary" />
        <el-tab-pane
          label="📚 Summary to Knowledge"
          name="summary_to_knowledge"
        />
      </el-tabs>

      <el-row :gutter="12" style="margin-bottom: 10px">
        <el-col :span="12">
          <div style="margin-bottom: 6px; font-weight: bold">
            🔵 Active Version ({{ currentVersion }})
          </div>
        </el-col>
        <el-col :span="12">
          <div style="margin-bottom: 6px; font-weight: bold">
            🟡 Compare With Version
          </div>
          <el-select
            v-model="compareVersion"
            placeholder="Select version to compare"
            size="small"
            style="width: 100%"
            @change="handleVersionChange"
          >
            <el-option
              v-for="item in promptVersions[activeTab].filter(
                (v) => v.template_version !== activePromptVersion
              )"
              :key="item.template_version"
              :label="item.template_version"
              :value="item.template_version"
            />
          </el-select>
        </el-col>
      </el-row>

      <el-row
        :gutter="12"
        v-if="promptVersions[activeTab].length"
        style="height: 600px"
      >
        <el-col :span="12" class="el-col">
          <VueMonacoDiffEditor
            v-if="currentPromptText && comparePromptText"
            :original="currentPromptText"
            :modified="comparePromptText"
            language="markdown"
            theme="vs"
            :options="{
              readOnly: true,
              wordWrap: 'on',
              wrappingStrategy: 'advanced',
              automaticLayout: true,
              wrappingIndent: 'same',
              renderSideBySide: true,
            }"
          />
        </el-col>
        <el-col :span="12" class="el-col">
          <VueMonacoDiffEditor
            v-if="currentPromptText && comparePromptText"
            :original="comparePromptText"
            :modified="currentPromptText"
            language="markdown"
            theme="vs"
            :options="{
              readOnly: true,
              wordWrap: 'on',
              wrappingStrategy: 'advanced',
              automaticLayout: true,
              wrappingIndent: 'same',
              renderSideBySide: true,
            }"
          />
        </el-col>
      </el-row>
    </div>
    <div v-else>
      <el-empty description="No bot info found." />
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch, watchEffect } from "vue";
import api from "../services/apiService";
import { VueMonacoDiffEditor } from "@guolao/vue-monaco-editor";

const props = defineProps({
  groupId: String,
  visible: Boolean,
  aiBots: Array,
});

const emit = defineEmits(["update:visible", "promptLoaded"]);

const bot = ref(null);

const activeTab = ref("cognitive_guidance");
const currentVersion = ref("");
const compareVersion = ref("");

const promptVersions = ref({
  cognitive_guidance: [],
  real_time_summary: [],
  summary_to_knowledge: [],
});

const activePromptVersion = computed(() => {
  const list = promptVersions.value[activeTab.value] || [];
  return list.find((v) => v.is_active)?.template_version || "";
});

const currentPromptText = computed(() => {
  const list = promptVersions.value[activeTab.value] || [];
  return (
    list.find((v) => v.template_version === currentVersion.value)
      ?.rendered_prompt || ""
  );
});
const comparePromptText = computed(() => {
  const list = promptVersions.value[activeTab.value] || [];
  return (
    list.find((v) => v.template_version === compareVersion.value)
      ?.rendered_prompt || ""
  );
});

const handleVersionChange = () => {
  const currentList = promptVersions.value[activeTab.value] || [];
  const current = currentList.find(
    (v) => v.template_version === currentVersion.value
  );
  const compare = currentList.find(
    (v) => v.template_version === compareVersion.value
  );

  if (current && compare) {
    console.log("🔁 Current version selected:", current.template_version);
    console.log("🔁 Compare version selected:", compare.template_version);
  } else {
    console.warn("⚠️ One or both selected versions are not found");
  }
};

watch(
  [() => props.groupId, () => props.aiBots],
  async ([newGroupId, bots]) => {
    const matchedBot = bots.find((b) => b.group_id === newGroupId);

    if (newGroupId && matchedBot) {
      bot.value = matchedBot;
      const botId = matchedBot.id;
      try {
        const cg = await api.getPromptVersions(botId, "cognitive_guidance");
        const rs = await api.getPromptVersions(botId, "real_time_summary");
        const sk = await api.getPromptVersions(botId, "summary_to_knowledge");

        emit("promptLoaded", {
          botId,
          cognitive_guidance: cg,
          real_time_summary: rs,
          summary_to_knowledge: sk,
        });

        promptVersions.value = {
          cognitive_guidance: cg,
          real_time_summary: rs,
          summary_to_knowledge: sk,
        };
      } catch (e) {
        console.error("❌ Failed to load prompt versions:", e);
      }
    }
  },
  { immediate: true }
);

watchEffect(() => {
  const versions = promptVersions.value[activeTab.value] || [];
  currentVersion.value = activePromptVersion.value;
  const otherVersions = versions.filter(
    (v) => v.template_version !== activePromptVersion.value
  );
  compareVersion.value = otherVersions[0]?.template_version || "";
});
</script>

<style scoped>
.prompt-box {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  white-space: pre-wrap;
  margin-bottom: 16px;
}
.version-tabs {
  margin-top: 20px;
}
.el-col {
  overflow: auto;
}
.el-select {
  margin-bottom: 10px;
}
</style>
