<template>
  <div class="group-overview">
    <div class="group-overview-bar">
      <div class="top-row">
        <div style="display: flex; flex-direction: column">
          <div class="left-info">
            <el-select
              v-model="localSelectedGroupId"
              class="group-select"
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
            <span class="goal" v-if="goal"
              ><span class="goal-label">目标：</span>{{ goal }}</span
            >
          </div>
        </div>
        <div class="right-info">
          <el-space>
            <el-tag
              v-for="(member, index) in members"
              :key="index"
              type="success"
              size="small"
            >
              {{ member.name }}
            </el-tag>
          </el-space>
        </div>
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
  routeName: String, // 新增
});

const emit = defineEmits(["updateGroup"]);

const handleGroupChange = (newId) => {
  emit("updateGroup", newId);
};

const localSelectedGroupId = ref(props.selectedGroupId);

// 监听 routeName 和 allGroups，自动匹配 group
watch(
  [() => props.routeName, () => props.allGroups],
  ([newRouteName, newAllGroups]) => {
    if (newRouteName && Array.isArray(newAllGroups)) {
      const match = newAllGroups.find(g => g.name === newRouteName);
      if (match) {
        localSelectedGroupId.value = match.id;
        handleGroupChange(match.id);
      }
    }
  },
  { immediate: true }
);


</script>

<style scoped>
.group-overview {
  width: 100%;
}

.group-overview-bar {
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.5rem 0.5rem 0.5rem;
  background-color: #fff;
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
  margin-top: 6px;
}

.session-title {
  font-size: 1.3rem;
  font-weight: 500;
  color: #555;
  margin-top: 10px;
  margin-bottom: 0;
  letter-spacing: 0.2px;
  line-height: 1.4;
}

.left-info {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 1.5rem;
}

.right-info {
  display: flex;
  gap: 0.9rem;
  align-items: center;
  flex-wrap: wrap;
}

.el-tag {
  display: flex;
  align-items: center;
}

.right-info > .el-tag:last-child {
  margin-left: 0.7rem;
}

.group-title {
  font-weight: 700;
  font-size: 1.18rem;
  color: #303133;
}

.goal {
  font-size: 0.88rem;
  font-weight: 400;
  color: #555;
  margin-left: 12px;
  line-height: 1.4;
}

.goal-label {
  color: #d4913a;
  font-weight: 500;
}

.group-select {
  width: 180px;
  margin-bottom: 0;
  font-size: 1rem;
}
</style>
