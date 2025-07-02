<template>
  <div class="history-section">
    <div class="history-header">
      <div class="history-title">历史异常反馈</div>
      <el-button size="small" type="primary" @click="loadHistoryData" :loading="historyLoading">刷新</el-button>
    </div>
    <div class="history-content">
      <el-table
        :data="anomalyHistory"
        style="width: 100%"
        v-loading="historyLoading"
        height="450"
      >
        <el-table-column prop="created_at" label="时间" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要">
          <template #default="scope">
            <span v-html="scope.row.summary"></span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="scope">
            <el-button size="small" @click="emitViewDetail(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top: 12px; text-align: right"
        background
        layout="prev, pager, next, jumper, ->, total"
        :current-page="historyPage"
        :page-size="historyPageSize"
        :total="historyTotal"
        @current-change="onHistoryPageChange"
        @size-change="onHistoryPageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import api from "@/services/apiService";

const props = defineProps({
  userId: String,
  groupId: String,
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
  return d.toLocaleString();
}

function emitViewDetail(row) {
  let parsed = null;
  if (row && row.raw_response) {
    let jsonStr = row.raw_response.trim();
    if (jsonStr.startsWith('```json')) {
      jsonStr = jsonStr.replace(/^```json|```$/g, '').trim();
    }
    try {
      parsed = JSON.parse(jsonStr);
    } catch (e) {
      console.error('❌ 解析历史异常 raw_response 失败:', e, jsonStr);
    }
  }
  const detailWithId = {
    ...parsed,
    id: row.id,
    created_at: row.created_at,
    summary: row.summary
  };
  emit("view-detail", detailWithId);
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
</style> 