<template>
  <div class="group-overview">
    <div class="group-overview-bar">
      <div class="top-row">
        <div style="display: flex; flex-direction: column">
          <div class="left-info">
            <el-select
              v-model="localSelectedGroupId"
              class="group-select"
              size="small"
              @change="handleGroupChange"
              placeholder="请选择小组"
            >
              <el-option
                v-for="g in allGroups"
                :key="g.id"
                :label="g.name"
                :value="g.id"
              />
            </el-select>
            <span class="goal" v-if="goal">目标：{{ goal }}</span>
          </div>
        </div>
        <div class="right-info">
          <el-space>
            <el-tag
              v-for="(member, index) in members"
              :key="index"
              size="small"
              type="success"
            >
              {{ member.name }}
            </el-tag>
          </el-space>
        </div>
      </div>
      <div class="session-row">
        <div class="session-name">{{ sessionTitle }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";

const props = defineProps({
  group: Object,
  members: Array,
  goal: String,
  sessionTitle: String,
  sessionId: String,
  allGroups: Array,
  selectedGroupId: String,
});

const emit = defineEmits(["updateGroup"]);

const localSelectedGroupId = ref(props.selectedGroupId);

watch(
  () => props.selectedGroupId,
  (val) => {
    localSelectedGroupId.value = val;
  }
);

const handleGroupChange = (newId) => {
  emit("updateGroup", newId);
};


</script>

<style scoped>
.group-overview {
  width: 100%;
}

.group-overview-bar {
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 0.75rem 1.25rem;
  font-size: 14px;
  background-color: #ffffff;
  border-radius: 12px;
  box-sizing: border-box;
  font-family: "Helvetica Neue", Arial, sans-serif;
}

.top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  width: 100%;
}

.session-row {
  width: 100%;
  text-align: center;
  margin-top: 4px;
}

.session-name {
  padding-top: 1rem;
  font-size: 18px;
  font-weight: 500;
  color: #000;
}

.left-info {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 1rem;
  min-height: 32px;
}

.right-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.right-info > .el-tag:last-child {
  margin-left: 0.5rem;
}

.group-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.goal {
  font-size: 14px;
  color: #606266;
}

.group-select {
  width: 160px;
  margin-bottom: 0;
}
</style>
