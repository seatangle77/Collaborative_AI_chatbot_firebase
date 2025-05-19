<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="(val) => emit('update:visible', val)"
    title="🧠 Personal Agent Prompt Details"
    size="70%"
    direction="rtl"
    :with-header="true"
  >
    <div v-if="user">
      <h3>{{ user.name }}</h3>
      <p style="margin-bottom: 10px">
        {{ user.academic_advantages || "No academic info available." }}
      </p>
    </div>

    <el-tabs v-model="activeTab" style="margin-top: 20px">
      <el-tab-pane label="📘 Term Explanation" name="term_explanation" />
      <el-tab-pane label="📗 Knowledge Follow-up" name="knowledge_followup" />
    </el-tabs>

    <el-row :gutter="10" style="margin-top: 20px">
      <el-col :span="12"></el-col>
      <el-col :span="12">
        <el-select
          v-model="compareVersion"
          placeholder="Compare with version..."
          size="small"
          class="version-select"
        >
          <el-option
            v-for="item in availableVersions.filter(
              (v) => v.template_version !== activeVersion?.template_version
            )"
            :key="item.template_version"
            :label="item.template_version"
            :value="item.template_version"
          />
        </el-select>
      </el-col>
    </el-row>

    <el-row
      v-if="activeVersion && comparePromptText"
      style="margin-top: 20px; height: 500px"
      :gutter="10"
    >
      <el-col :span="12">
        <h4 class="editor-header">
          🔵 Active Version ({{ activeVersion.template_version }})
        </h4>
        <VueMonacoDiffEditor
          :original="''"
          :modified="activeVersion.rendered_prompt"
          language="markdown"
          theme="vs"
          :options="{
            readOnly: true,
            wordWrap: 'on',
            automaticLayout: true,
          }"
        />
      </el-col>
      <el-col :span="12">
        <h4>🟡 Compare Version ({{ compareVersion }})</h4>
        <VueMonacoDiffEditor
          :original="''"
          :modified="comparePromptText"
          language="markdown"
          theme="vs"
          :options="{
            readOnly: true,
            wordWrap: 'on',
            automaticLayout: true,
          }"
        />
      </el-col>
    </el-row>

    <el-empty v-else description="No prompt available for this tab." />
  </el-drawer>
</template>

<script setup>
import { ref, computed, watchEffect } from "vue";
import { VueMonacoDiffEditor } from "@guolao/vue-monaco-editor";

const props = defineProps({
  user: Object,
  agentId: String,
  visible: Boolean,
  promptVersions: Object,
});

const emit = defineEmits(["update:visible"]);

const activeTab = ref("term_explanation");
const compareVersion = ref("");

const availableVersions = computed(() => {
  return props.promptVersions?.[activeTab.value] || [];
});

const activeVersion = computed(() => {
  return availableVersions.value.find((v) => v.is_active);
});

const comparePromptText = computed(() => {
  return (
    availableVersions.value.find(
      (v) => v.template_version === compareVersion.value
    )?.rendered_prompt || ""
  );
});

watchEffect(() => {
  if (
    !compareVersion.value &&
    availableVersions.value.length > 1 &&
    activeVersion.value
  ) {
    const firstNonActive = availableVersions.value.find(
      (v) => v.template_version !== activeVersion.value.template_version
    );
    if (firstNonActive) {
      compareVersion.value = firstNonActive.template_version;
    }
  }
});
</script>

<style scoped>
.el-col {
  overflow: auto;
}

.version-select {
  width: 100%;
  margin-bottom: 8px;
}
</style>
