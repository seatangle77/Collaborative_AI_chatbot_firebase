<template>
  <div class="history-section">
    <div class="history-header">
      <div class="history-title">{{ title }}</div>
      <el-button size="small" type="primary" @click="loadHistoryData" :loading="historyLoading">刷新</el-button>
    </div>
    <div class="history-content">
      <el-table
        :data="anomalyHistory"
        style="width: 100%"
        v-loading="historyLoading"
        height="500"
        @row-click="emitViewDetail"
      >
        <el-table-column prop="created_at" label="时间" width="80">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要">
          <template #default="scope">
            <span v-html="scope.row.summary"></span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        size="small"
        background
        layout="prev, pager, next"
        :current-page="historyPage"
        :page-size="historyPageSize"
        :total="historyTotal"
        @current-change="onHistoryPageChange"
        @size-change="onHistoryPageSizeChange"
      />
    </div>
    <!-- 右下角悬浮卡片/小窗 -->
    <!-- 已移除浮窗相关代码 -->
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import api from "@/services/apiService";
import { ElNotification } from 'element-plus';

const props = defineProps({
  userId: String,
  groupId: String,
  title: {
    type: String,
    default: "历史异常反馈"
  }
});
const emit = defineEmits(["view-detail"]);

const anomalyHistory = ref([]);
const historyPage = ref(1);
const historyPageSize = ref(10);
const historyTotal = ref(0);
const historyLoading = ref(false);

function loadHistoryData(page = historyPage.value, pageSize = historyPageSize.value) {
  if (!props.groupId || !props.userId) return;
  historyLoading.value = true;
  api.getAnomalyResultsByUser(props.groupId, props.userId, page, pageSize)
    .then(res => {
      anomalyHistory.value = res.results || [];
      historyTotal.value = res.total || 0;
      historyPage.value = res.page || 1;
      historyPageSize.value = res.page_size || 10;
    })
    .catch(err => {
      console.error("❌ 加载历史异常反馈失败:", err);
    })
    .finally(() => {
      historyLoading.value = false;
    });
}

function onHistoryPageChange(page) {
  historyPage.value = page;
  loadHistoryData(page, historyPageSize.value);
}
function onHistoryPageSizeChange(size) {
  historyPageSize.value = size;
  historyPage.value = 1;
  loadHistoryData(1, size);
}

function formatDate(str) {
  if (!str) return '';
  const d = new Date(str);
  // 格式：MM/DD HH:mm:ss
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  const second = String(d.getSeconds()).padStart(2, '0');
  return `${month}/${day} ${hour}:${minute}:${second}`;
}

// 直接点击表格行时触发抽屉显示
function emitViewDetail(row) {
  emit("view-detail", row);
}

onMounted(() => {
  loadHistoryData();
});
watch([() => props.userId, () => props.groupId], () => {
  loadHistoryData();
});
</script>

<style scoped>
.history-section {
  flex: 1;
  min-width: 300px;
  max-width: 400px;
  background: #ffffff;
  padding: 16px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 46px;
  padding: 0 0 8px 0;
  box-sizing: border-box;
}

.history-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.5;
  display: flex;
  align-items: center;
  height: 100%;
}

.history-header .el-button {
  margin-left: 16px;
  height: 32px;
  line-height: 32px;
  padding: 0 16px;
  display: flex;
  align-items: center;
}

.history-content {
  height: calc(100vh - 400px);
  min-height: 400px;
}
:deep(.el-table) {
  table-layout: fixed !important;
  width: 100% !important;
  font-size: 13px;
}
:deep(.el-table th),
:deep(.el-table td) {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  max-width: 120px;
}
:deep(.el-pagination),
:deep(.el-button) {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:deep(.el-pagination.is-background) {
  min-width: 0;
  width: auto;
  margin: 12px 0 0 0;
  display: flex;
  justify-content: flex-start;
}
:deep(.el-table__body tr) {
  cursor: pointer;
}
/* 已移除 .float-card 相关样式 */
</style> 