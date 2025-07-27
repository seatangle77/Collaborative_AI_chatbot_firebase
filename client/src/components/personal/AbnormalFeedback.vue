<template>
  <div class="abnormal-feedback">
    <el-card v-if="shouldShow">
      <template #header>
        <div class="card-header">
          <span>提示反馈报告</span>
        </div>
      </template>
      <div class="main-section">
        <div class="summary-block">
          <span class="summary-label">提示总结：</span>
          <span
            class="summary-content"
            v-html="md2html(anomalyData.summary)"
          ></span>
        </div>
        <div v-if="anomalyData.detail" class="detail-block">
          <div v-if="anomalyData.user_name" class="detail-row">
            <span class="detail-label">用户：</span>
            <span class="detail-value user-name">{{ anomalyData.user_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">提示类型：</span>
            <span
              class="detail-value type"
              v-html="md2html(translateLevelType(anomalyData.detail.type))"
            ></span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态描述：</span>
            <span
              class="detail-value"
              v-html="md2html(anomalyData.detail.status)"
            ></span>
          </div>
          <div class="detail-row evidence-row">
            <span class="detail-label">证据：</span>
            <span
              class="detail-value evidence"
              v-html="md2html(translateLevelType(anomalyData.detail.evidence))"
            ></span>
          </div>
          <div class="detail-row suggestion-row">
            <span class="detail-label">建议：</span>
            <span
              class="detail-value suggestion"
              v-html="md2html(anomalyData.detail.suggestion)"
            ></span>
          </div>
        </div>
        <div class="button-row">
          <el-button type="primary" @click="onMore" size="default" v-if="!showMore">
            More
          </el-button>
          <el-button type="primary" @click="onCollapse" size="default" v-else>
            Hide
          </el-button>
          <el-button
            type="primary"
            @click="onLess"
            size="default"
            style="margin-left: 8px"
            :disabled="props.anomalyData?.anomaly_analysis_results_id && lessClickedMap[props.anomalyData.anomaly_analysis_results_id]"
          >
            Less
          </el-button>
          <el-button
            type="success"
            @click="openShareDialog"
            size="default"
            style="margin-left: 8px"
          >
            Share
          </el-button>
        </div>
        <div v-if="showMore && (anomalyData.more_info || anomalyData.user_data_summary)" class="more-info">
          <div v-if="anomalyData.user_data_summary">
            <div
              ref="barChartRef"
              style="width: 100%; aspect-ratio: 1.6 / 1; max-width: 400px; min-width: 200px; margin: 0 auto 16px auto;"
            ></div>
            <div ref="radarChartRef" style="width: 100%; aspect-ratio: 1.6 / 1; max-width: 400px; min-width: 200px; margin: 0 auto;"></div>
          </div>
          <div v-if="!anomalyData.more_info && anomalyData.user_data_summary" class="info-block">
            <span class="info-label">提示：</span>
            <span class="info-content">当前显示的是用户行为数据图表，详细的分析信息将在后续更新中提供。</span>
          </div>
          <el-divider v-if="anomalyData.more_info" />
          <div v-if="anomalyData.more_info?.detailed_reason" class="info-block">
            <span class="info-label">详细推理：</span>
            <span
              class="info-content"
              v-html="md2html(anomalyData.more_info.detailed_reason)"
            ></span>
          </div>
          <div v-if="anomalyData.more_info?.history_comparison" class="info-block">
            <span class="info-label">历史对比：</span>
            <template v-if="historyComparisonTable && historyComparisonTable.data.length">
              <el-table :data="historyComparisonTable.data" class="history-compare-table" style="width: 100%; margin-bottom: 8px;">
                <el-table-column
                  v-for="col in historyComparisonTable.columns"
                  :key="col.prop"
                  :prop="col.prop"
                  :label="col.label"
                  align="center"
                />
              </el-table>
            </template>
            <span
              v-else
              class="info-content"
              v-html="md2html(anomalyData.more_info.history_comparison)"
            ></span>
          </div>
          <div v-if="anomalyData.more_info?.group_comparison" class="info-block">
            <span class="info-label">组内对比：</span>
            <span
              class="info-content"
              v-html="md2html(anomalyData.more_info.group_comparison)"
            ></span>
          </div>
          <div v-if="anomalyData.more_info?.collaboration_suggestion" class="info-block">
            <span class="info-label">协作建议：</span>
            <span
              class="info-content"
              v-html="md2html(anomalyData.more_info.collaboration_suggestion)"
            ></span>
          </div>
          <div v-if="anomalyData.group_distribution" class="info-block">
            <span class="info-label">组内分布：</span>
            <div class="distribution-content">
              <div class="distribution-item" v-for="(count, type) in anomalyData.group_distribution" :key="type">
                <span class="distribution-type">{{ getDistributionTypeLabel(type) }}</span>
                <span class="distribution-count">{{ count }}人</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    <el-alert
      v-else-if="
        anomalyData &&
        anomalyData.score &&
        anomalyData.score['是否提示'] === false
      "
      type="info"
      title="暂无提示反馈"
      description="当前未检测到需要提示的情况。"
    />
    <el-alert
      v-else
      type="error"
      title="提示反馈数据缺失或格式错误"
      description="请检查后端返回内容格式是否正确。"
    />
    <!-- 分享选择弹窗 -->
    <el-dialog v-model="shareDialogVisible" title="选择要分享的组员" width="400px" @close="resetShareDialog">
      <el-checkbox-group v-model="selectedShareUserIds">
        <el-checkbox
          v-for="member in shareableMembers"
          :key="member.user_id"
          :label="member.user_id"
        >
          {{ member.name || member.user_id }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="shareDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="confirmShare">Share</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { marked } from "marked";
import api from '@/services/apiService';
import { translateLevelType, getDistributionTypeLabel } from '@/utils/levelTranslations';

const props = defineProps({
  anomalyData: Object,
  members: {
    type: Array,
    default: () => []
  }
});

const showMore = ref(false);
const barChartRef = ref(null);
const radarChartRef = ref(null);
let barChart = null;
let radarChart = null;

// 新增：记录哪些异常已点击过Less
const lessClickedMap = ref({});

const shouldShow = computed(() => {
  // 检查基本数据是否存在
  if (!props.anomalyData) return false;
  
  // 检查是否有score字段且是否提示为true
  if (props.anomalyData.score && props.anomalyData.score["should_notify"] === true) {
    return true;
  }
  
  // 如果没有score字段，但有基本的提示信息，也显示
  if (props.anomalyData.summary && props.anomalyData.detail) {
    return true;
  }
  
  // 对于历史记录，只要有summary就显示
  if (props.anomalyData.summary) {
    return true;
  }
  
  return false;
});

const sortedExtraSuggestions = computed(() => {
  const arr = props.anomalyData?.more_info?.extra_suggestions;
  if (Array.isArray(arr)) {
    return arr.slice().sort((a, b) => a.priority - b.priority);
  }
  return [];
});

function formatExtraSuggestions(str) {
  if (!str) return "";
  if (typeof str !== "string") {
    try {
      str = JSON.stringify(str, null, 2);
    } catch {
      return "";
    }
  }
  return str.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br/>");
}

// 动态引入 echarts
let echarts = null;
async function loadEcharts() {
  if (!echarts) {
    echarts = await import("echarts");
  }
}

function renderCharts() {
  if (!props.anomalyData?.user_data_summary) return;
  const data = props.anomalyData.user_data_summary;
  // 柱状图数据
  const barOption = {
    title: {
      text: "用户行为数据",
      left: "center",
      top: 10,
      textStyle: { fontSize: 15 },
    },
    tooltip: {},
    xAxis: {
      type: "category",
      data: ["发言", "引用/回复", "编辑", "浏览页面", "切换频率"],
    },
    yAxis: { type: "value" },
    series: [
      {
        data: [
          data.speaking_count,
          data.reply_count,
          data.edit_count,
          data.page_view_count,
          data.page_switch_frequency,
        ],
        type: "bar",
        itemStyle: { color: "#3478f6" },
        barWidth: 32,
      },
    ],
  };
  // 雷达图数据
  const radarOption = {
    title: {
      text: "与组内平均活跃度差值",
      left: "center",
      top: 10,
      textStyle: { fontSize: 15 },
    },
    tooltip: {},
    radar: {
      indicator: [
        { name: "发言差值", max: 10, min: -10 },
        { name: "回复差值", max: 10, min: -10 },
        { name: "编辑差值", max: 10, min: -10 },
        { name: "页面聚焦差值", max: 10, min: -10 },
      ],
      radius: 80,
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: [
              data.group_avg_comparison.speaking_diff,
              data.group_avg_comparison.reply_diff,
              data.group_avg_comparison.edit_diff,
              data.group_avg_comparison.page_focus_diff,
            ],
            name: "与组内平均差值",
            areaStyle: { color: "rgba(52,120,246,0.2)" },
            lineStyle: { color: "#3478f6" },
          },
        ],
      },
    ],
  };
  // 渲染
  if (barChartRef.value) {
    if (!barChart) barChart = echarts.init(barChartRef.value);
    barChart.setOption(barOption);
  }
  if (radarChartRef.value) {
    if (!radarChart) radarChart = echarts.init(radarChartRef.value);
    radarChart.setOption(radarOption);
  }
}

watch(
  () => showMore.value,
  async (val) => {
    if (val && props.anomalyData?.user_data_summary) {
      await loadEcharts();
      nextTick(() => {
        renderCharts();
      });
    }
  }
);

onMounted(async () => {
  if (showMore.value && props.anomalyData?.user_data_summary) {
    await loadEcharts();
    nextTick(() => {
      renderCharts();
    });
  }
});

// 分享弹窗相关
const shareDialogVisible = ref(false);
const selectedShareUserIds = ref([]);
const shareableMembers = computed(() => {
  const anomaly = props.anomalyData || {};
  return props.members.filter(m => m.user_id !== anomaly.user_id);
});
function openShareDialog() {
  // 默认都不勾选
  selectedShareUserIds.value = [];
  shareDialogVisible.value = true;
}
function resetShareDialog() {
  selectedShareUserIds.value = [];
}
async function confirmShare() {
  if (!selectedShareUserIds.value.length) {
    ElMessage.warning('请选择要分享的组员');
    return;
  }
  shareDialogVisible.value = false;
  await callFeedbackClick('Share', selectedShareUserIds.value);
}

async function callFeedbackClick(clickType, customShareUserIds) {
  const anomaly = props.anomalyData || {};
  
  // 校验必填字段
  if (!anomaly.group_id || !anomaly.user_id) {
    ElMessage.error('反馈参数缺失：group_id 或 user_id');
    return;
  }
  if (!anomaly.anomaly_analysis_results_id) {
    ElMessage.error('反馈参数缺失：anomaly_analysis_results_id');
    return;
  }
  if (!anomaly.detail || !anomaly.detail.type || !anomaly.detail.status) {
    ElMessage.error('反馈参数缺失：异常类型或状态');
    return;
  }

  // 如果是Share，自动获取所有其他组员的ID（现在改为用customShareUserIds）
  let shareToUserIds = [];
  if (clickType === 'Share') {
    if (Array.isArray(customShareUserIds)) {
      shareToUserIds = customShareUserIds;
    } else {
      const currentUserId = anomaly.user_id;
      shareToUserIds = props.members
        .filter(member => member.user_id !== currentUserId)
        .map(member => member.user_id);
    }
    if (shareToUserIds.length === 0) {
      ElMessage.warning('没有其他组员可以分享');
      return;
    }
  }

  const payload = {
    group_id: String(anomaly.group_id),
    user_id: String(anomaly.user_id),
    click_type: clickType,
    anomaly_analysis_results_id: String(anomaly.anomaly_analysis_results_id),
    detail_type: String(translateLevelType(anomaly.detail.type)),
    detail_status: String(translateLevelType(anomaly.detail.status)),
    share_to_user_ids: shareToUserIds,
  };

  try {
    await api.feedbackClick(payload);
    if (clickType === 'Less') {
      ElMessage.info('已降低后续异常提示频率');
      // 记录该异常已点击过Less
      if (anomaly.anomaly_analysis_results_id) {
        lessClickedMap.value[anomaly.anomaly_analysis_results_id] = true;
      }
    } else if (clickType === 'Share') {
      ElMessage.success(`已成功分享给 ${shareToUserIds.length} 个组员`);
    }
  } catch (e) {
    ElMessage.error('反馈记录失败');
  }
}

function onMore() {
  showMore.value = true;
  callFeedbackClick('More');
}
function onCollapse() {
  showMore.value = false;
}
function onLess() {
  showMore.value = false;
  // 只允许点击一次
  const anomaly = props.anomalyData || {};
  if (anomaly.anomaly_analysis_results_id && lessClickedMap.value[anomaly.anomaly_analysis_results_id]) {
    ElMessage.warning('该异常已反馈过Less，不能重复操作');
    return;
  }
  callFeedbackClick('Less');
}
function shareFeedback() {
  // 旧的直接分享逻辑已废弃
  // callFeedbackClick('Share');
  openShareDialog();
}

// markdown 转 html 工具
function md2html(str) {
  if (!str) return "";
  return marked.parse(str);
}

// 解析 markdown 表格为结构化数据
function parseMarkdownTable(md) {
  if (!md) return null;
  const lines = md.trim().split('\n').filter(l => l.trim());
  if (lines.length < 2) return null;
  // 取表头
  const headerLine = lines[0].replace(/^\||\|$/g, '');
  const headers = headerLine.split('|').map(h => h.trim());
  // 过滤掉分隔线
  const dataLines = lines.slice(2);
  const data = dataLines.map(line => {
    const cells = line.replace(/^\||\|$/g, '').split('|').map(c => c.trim());
    const row = {};
    headers.forEach((h, i) => {
      row[h] = cells[i] || '';
    });
    return row;
  });
  return {
    columns: headers.map(h => ({ prop: h, label: h })),
    data
  };
}

const historyComparisonTable = computed(() => {
  const md = props.anomalyData?.more_info?.history_comparison;
  return parseMarkdownTable(md);
});


</script>

<style scoped>
.abnormal-feedback {
  padding: 8px;
  background-color: #fffbe6;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
}
.card-header {
  font-weight: bold;
  font-size: 16px;
  color: #2c3e50;
}
.main-section {
  padding: 0;
}
.summary-block,
.detail-block,
.button-row {
  padding: 8px 0;
}
.summary-block {
  background: #f0f6ff;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #1a237e;
  display: flex;
  align-items: center;
  min-height: 32px;
}
.more-info {
  margin-top: 8px;
  padding: 8px 0;
}
.info-block {
  margin-bottom: 6px;
  padding-bottom: 2px;
}
.summary-label {
  color: #3478f6;
  min-width: 80px;
  display: inline-block;
  font-size: 13px;
  line-height: 1.6;
  vertical-align: middle;
}
.summary-content {
  color: #222;
  font-size: 13px;
  line-height: 1.6;
  vertical-align: middle;
}
.detail-block {
  background: #fff;
  border-radius: 6px;
  padding: 12px 16px 8px 16px;
  margin-bottom: 5px;
  box-shadow: 0 1px 3px rgba(52, 120, 246, 0.06);
}
.detail-row {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}
.detail-label {
  min-width: 80px;
  color: #888;
  font-weight: 500;
  display: inline-block;
  font-size: 13px;
  line-height: 1.6;
  vertical-align: middle;
}
.detail-value {
  color: #222;
  font-weight: 400;
  font-size: 13px;
  line-height: 1.6;
  vertical-align: middle;
  display: block;
  word-break: break-all;
}
.detail-row .detail-value :first-child {
  margin: 0 !important;
}
.type {
  color: #e67e22;
  font-weight: 600;
}
.evidence-row .evidence {
  background: #fffbe6;
  border-radius: 4px;
  padding: 5px 5px;
  color: #b26a00;
}
.suggestion-row .suggestion {
  background: #e3f9e5;
  border-radius: 4px;
  padding: 2px 6px;
  color: #218838;
}
.more-info {
  margin-top: 16px;
  background: #f9f9f9;
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 13px;
  color: #444;
}
.info-block {
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #e0e0e0;
}
.info-label {
  color: #3478f6;
  font-weight: 500;
  margin-right: 6px;
}
.info-content {
  color: #222;
}
.info-content table tr {
  border-bottom: 1px solid #d0d7de !important;
}
.info-content th,
.summary-content th {
  background: #f0f6ff;
  font-weight: 600;
  color: #3478f6;
}
.el-table.history-compare-table {
  font-size: 13px;
  background: #f9f9f9;
  border-radius: 0;
  border: none;
}
.el-table.history-compare-table th {
  background: #f0f6ff !important;
  color: #3478f6 !important;
  font-weight: 600;
  border: none !important;
  text-align: center;
}
.el-table.history-compare-table td {
  background: #f9f9f9 !important;
  color: #222 !important;
  border: none !important;
  text-align: center;
}
.el-table.history-compare-table tr {
  border-bottom: 1px solid #d0d7de !important;
}
.el-table.history-compare-table .el-table__body tr:last-child td {
  border-bottom: none !important;
}
:deep(.el-table.history-compare-table .cell) {
  line-height: 18px;
  padding: 2px 6px;
}
:deep(.el-table.history-compare-table),
:deep(.el-table.history-compare-table .el-table__body),
:deep(.el-table.history-compare-table .el-table__row),
:deep(.el-table.history-compare-table .el-table__cell),
:deep(.el-table.history-compare-table .cell),
:deep(.el-table.history-compare-table td) {
  background: #f9f9f9 !important;
  color: #222 !important;
}
:deep(.el-table.history-compare-table thead) {
  background: #f0f6ff !important;
}
:deep(.el-table.history-compare-table th) {
  background: #f0f6ff !important;
  color: #222 !important;
  font-weight: 600;
}
:deep(.el-card__header) {
  font-size: 18px;
  font-weight: bold;
  color: #1a237e;
  border-bottom: 1px solid #e4e7ed;
  padding: 10px 15px;
}
:deep(.el-card__body) {
  padding: 10px 15px;
  background: #fafbfc;
  border-radius: 0 0 8px 8px;
  margin-top: 2px;
}
:deep(.evidence-row .evidence ul) {
  margin: 4px 0 4px 16px !important;
  padding-left: 16px !important;
  list-style-type: disc !important;
  font-size: 13px !important;
}
:deep(.evidence-row .evidence li) {
  margin-bottom: 2px !important;
  line-height: 1.5 !important;
  color: #444 !important;
  padding-left: 2px !important;
}

.distribution-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.distribution-item {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f0f6ff;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
}

.distribution-type {
  color: #3478f6;
  font-weight: 500;
}

.distribution-count {
  color: #666;
  font-weight: 600;
}

.user-name {
  color: #3478f6;
  font-weight: 600;
}
</style>
