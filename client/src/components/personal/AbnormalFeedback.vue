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
            v-html="md2html(anomalyData.glasses_summary || anomalyData.summary)"
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
              v-html="md2html(highlightNumbers(anomalyData.detail.evidence))"
            ></span>
          </div>
          <div class="detail-row suggestion-row" v-if="anomalyData.detail.suggestion">
            <span class="detail-label">建议：</span>
            <span
              class="detail-value suggestion"
              v-html="md2html(anomalyData.detail.suggestion)"
            ></span>
          </div>
        </div>
        <div class="button-row">
          <el-button 
            type="primary" 
            @click="onMore" 
            size="default" 
            v-if="!showMore"
            :loading="buttonLoadingMap.more"
            :disabled="buttonLoadingMap.more"
          >
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
            :loading="buttonLoadingMap.less"
            :disabled="buttonLoadingMap.less"
          >
            Less
          </el-button>
          <el-button
            type="success"
            @click="openShareDialog"
            size="default"
            style="margin-left: 8px"
            :loading="buttonLoadingMap.share"
            :disabled="buttonLoadingMap.share"
          >
            Share
          </el-button>
        </div>
        <div v-if="showMore && (anomalyData.more_info || anomalyData.user_data_summary)" class="more-info">
          
          <!-- More Info 图表区域 -->
          <div v-if="anomalyData.more_info" class="charts-section">
            <div class="charts-header">
              <span class="charts-title">📊 数据分析图表</span>
            </div>
            <div class="charts-grid">
              <!-- 参与度分布饼图 -->
              <div class="chart-container" v-if="anomalyData.group_distribution">
                <div ref="participationChartRef" class="chart-item"></div>
                <div class="chart-title">组内参与度分布</div>
              </div>
              <!-- 行为指标柱状图 -->
              <div class="chart-container" v-if="anomalyData.more_info.extra_data">
                <div ref="behaviorChartRef" class="chart-item"></div>
                <div class="chart-title">行为指标对比</div>
              </div>
            </div>
          </div>
          
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
          <div v-if="anomalyData.group_distribution?.action_hint" class="info-block">
            <span class="info-label">组内建议：</span>
            <span
              class="info-content"
              v-html="md2html(anomalyData.group_distribution.action_hint)"
            ></span>
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
        <el-button @click="shareDialogVisible = false" :disabled="buttonLoadingMap.share">Cancel</el-button>
        <el-button 
          type="primary" 
          @click="confirmShare" 
          :loading="buttonLoadingMap.share"
          :disabled="buttonLoadingMap.share"
        >
          Share
        </el-button>
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

const emit = defineEmits(['updateReminderFrequency']);

const showMore = ref(false);
const barChartRef = ref(null);
const radarChartRef = ref(null);
const participationChartRef = ref(null);
const behaviorChartRef = ref(null);
let barChart = null;
let radarChart = null;
let participationChart = null;
let behaviorChart = null;

// 按钮加载状态管理
const buttonLoadingMap = ref({
  more: false,
  less: false,
  share: false
});



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

// 渲染more_info图表
function renderMoreInfoCharts() {
  if (!props.anomalyData?.more_info) return;
  
  // 参与度分布饼图
  if (participationChartRef.value && props.anomalyData.group_distribution) {
    const distribution = props.anomalyData.group_distribution;
    const pieData = [
      { value: distribution.high || 0, name: '高参与', itemStyle: { color: '#52c41a' } },
      { value: distribution.normal || 0, name: '正常参与', itemStyle: { color: '#1890ff' } },
      { value: distribution.low || 0, name: '低参与', itemStyle: { color: '#faad14' } },
      { value: distribution.no || 0, name: '无参与', itemStyle: { color: '#ff4d4f' } },
      { value: distribution.dominant || 0, name: '主导型', itemStyle: { color: '#722ed1' } }
    ].filter(item => item.value > 0);
    
    const pieOption = {
      title: {
        text: '组内成员参与度分布',
        left: 'center',
        top: 10,
        textStyle: { fontSize: 12, fontWeight: 'bold' }
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          const total = pieData.reduce((sum, item) => sum + item.value, 0);
          const percentage = ((params.value / total) * 100).toFixed(1);
          return `${params.name}<br/>人数: ${params.value}人<br/>占比: ${percentage}%`;
        }
      },
      legend: {
        orient: 'vertical',
        left: '3%',
        top: 'center',
        textStyle: { fontSize: 11 },
        itemWidth: 12,
        itemHeight: 8,
        itemGap: 8,
        formatter: function(name) {
          const item = pieData.find(d => d.name === name);
          if (item) {
            return `${name} (${item.value}人)`;
          }
          return name;
        }
      },
      series: [
        {
          name: '参与度分布',
          type: 'pie',
          radius: ['30%', '55%'],
          center: ['70%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: true,
            position: 'outside',
            formatter: '{b}\n{c}人 ({d}%)',
            fontSize: 10,
            color: '#333'
          },
          labelLine: {
            show: true,
            length: 12,
            length2: 12
          },
          data: pieData
        }
      ]
    };
    
    if (!participationChart) participationChart = echarts.init(participationChartRef.value);
    participationChart.setOption(pieOption);
  }
  
  // 行为指标柱状图
  if (behaviorChartRef.value && props.anomalyData.more_info.extra_data) {
    const extraData = parseExtraData(props.anomalyData.more_info.extra_data);
    const barOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '8%',
        right: '8%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['鼠标操作', '鼠标时长(秒)', '总分'],
        axisLabel: { fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { fontSize: 11 }
      },
      series: [
        {
          name: '数值',
          type: 'bar',
          data: [
            { value: extraData.mouse_action_count || 0, itemStyle: { color: '#1890ff' } },
            { value: extraData.mouse_duration_seconds || 0, itemStyle: { color: '#52c41a' } },
            { value: extraData.total_score || 0, itemStyle: { color: '#faad14' } }
          ],
          barWidth: '60%'
        }
      ]
    };
    
    if (!behaviorChart) behaviorChart = echarts.init(behaviorChartRef.value);
    behaviorChart.setOption(barOption);
  }
}



watch(
  () => showMore.value,
  async (val) => {
    if (val) {
      await loadEcharts();
      nextTick(() => {
        if (props.anomalyData?.user_data_summary) {
          renderCharts();
        }
        if (props.anomalyData?.more_info) {
          renderMoreInfoCharts();
        }
      });
    }
  }
);

onMounted(async () => {
  if (showMore.value) {
    await loadEcharts();
    nextTick(() => {
      if (props.anomalyData?.user_data_summary) {
        renderCharts();
      }
      if (props.anomalyData?.more_info) {
        renderMoreInfoCharts();
      }
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
  if (!anomaly.record_id) {
    ElMessage.error('反馈参数缺失：record_id');
    return;
  }
  if (!anomaly.detail || !anomaly.detail.type || !anomaly.detail.status) {
    ElMessage.error('反馈参数缺失：异常类型或状态');
    return;
  }

  // 设置按钮加载状态
  const buttonKey = clickType.toLowerCase();
  if (buttonLoadingMap.value[buttonKey]) {
    return; // 如果按钮正在加载中，直接返回
  }
  buttonLoadingMap.value[buttonKey] = true;

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
      buttonLoadingMap.value[buttonKey] = false;
      return;
    }
  }

  const payload = {
    group_id: String(anomaly.group_id),
    user_id: String(anomaly.user_id),
    click_type: clickType,
    anomaly_analysis_results_id: String(anomaly.record_id),
    detail_type: String(translateLevelType(anomaly.detail.type)),
    detail_status: String(translateLevelType(anomaly.detail.status)),
    share_to_user_ids: shareToUserIds,
  };

  try {
    const response = await api.feedbackClick(payload);
    if (clickType === 'Less') {
      const intervalMinutes = Math.round(response.feedback_setting?.interval_seconds / 60);
      ElMessage({
        message: `已降低后续异常提示频率，当前提醒间隔：${intervalMinutes}分钟`,
        type: 'success',
        duration: 3000,
        customClass: 'custom-feedback-message'
      });
      // 通知父组件更新提醒频率
      console.log('📤 发送更新提醒频率事件 (Less):', intervalMinutes);
      emit('updateReminderFrequency', intervalMinutes);
    } else if (clickType === 'More') {
      const intervalMinutes = Math.round(response.feedback_setting?.interval_seconds / 60);
      ElMessage({
        message: `已提高后续异常提示频率，当前提醒间隔：${intervalMinutes}分钟`,
        type: 'success',
        duration: 3000,
        customClass: 'custom-feedback-message'
      });
      // 通知父组件更新提醒频率
      console.log('📤 发送更新提醒频率事件 (More):', intervalMinutes);
      emit('updateReminderFrequency', intervalMinutes);
    } else if (clickType === 'Share') {
      ElMessage.success(`已成功分享给 ${shareToUserIds.length} 个组员`);
    }
  } catch (e) {
    ElMessage.error('反馈记录失败');
  } finally {
    // 无论成功还是失败，都要重置按钮加载状态
    buttonLoadingMap.value[buttonKey] = false;
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

// 高亮数字函数，用不同颜色标记
function highlightNumbers(text) {
  if (!text) return '';
  
  console.log('原始文本:', text); // 调试用
  
  // 先处理所有特定格式，避免重复匹配
  text = text.replace(/时长：(\d+)s/g, '时长：<span class="number-time">$1</span>s');
  text = text.replace(/浏览时长：(\d+)s/g, '浏览时长：<span class="number-time">$1</span>s');
  text = text.replace(/占比：(\d+\.?\d*)%/g, '占比：<span class="number-percent">$1</span>%');
  text = text.replace(/次数：(\d+)/g, '次数：<span class="number-count">$1</span>');
  text = text.replace(/字符数：(\d+)/g, '字符数：<span class="number-chars">$1</span>');
  text = text.replace(/页面数：(\d+)/g, '页面数：<span class="number-pages">$1</span>');
  
  // 不再处理其他数字，避免嵌套问题
  // text = text.replace(/(\d+)/g, '<span class="number-other">$1</span>');
  
  console.log('处理后文本:', text); // 调试用
  
  return text;
}

// 解析extra_data字符串
function parseExtraData(extraDataStr) {
  if (!extraDataStr) return {};
  
  const result = {};
  const pairs = extraDataStr.split(', ');
  
  pairs.forEach(pair => {
    const [key, value] = pair.split(': ');
    if (key && value !== undefined) {
      // 处理数值
      if (value.includes('s') && !isNaN(parseFloat(value))) {
        result[key] = parseFloat(value);
        result[`${key}_seconds`] = parseFloat(value);
      } else if (value.includes('%') && !isNaN(parseFloat(value))) {
        result[key] = parseFloat(value);
        result[`${key}_percent`] = parseFloat(value);
      } else if (!isNaN(parseFloat(value))) {
        result[key] = parseFloat(value);
      } else {
        result[key] = value;
      }
    }
  });
  
  return result;
}




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

.suggestion-row .suggestion {
  background: #e3f9e5;
  border-radius: 4px;
  padding: 2px 6px;
  color: #218838;
}
.more-info {
  background: #f9f9f9;
  border-radius: 6px;
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
.evidence-row .evidence {
  background: #fffbe6;
  border-radius: 4px;
  padding: 5px 5px;
  color: #b26a00;
}

/* 数字高亮样式 - 统一颜色 */
:deep(.number-time),
:deep(.number-percent),
:deep(.number-count),
:deep(.number-chars),
:deep(.number-pages),
:deep(.number-other) {
  color: #1890ff !important;
  font-weight: bold !important;
  font-size: 14px !important;
}

/* 图表样式 */
.charts-section {
  margin-bottom: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.charts-header {
  margin-bottom: 16px;
  text-align: center;
}

.charts-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-item {
  width: 100%;
  height: 250px;
}

.chart-title {
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: #495057;
  margin-top: 6px;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
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



.user-name {
  color: #3478f6;
  font-weight: 600;
}

/* 自定义反馈消息样式 */
:deep(.custom-feedback-message) {
  min-width: 400px !important;
  padding: 16px 20px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

:deep(.custom-feedback-message .el-message__content) {
  font-size: 16px !important;
  line-height: 1.5 !important;
  font-weight: 500 !important;
}

:deep(.custom-feedback-message .el-message__icon) {
  font-size: 18px !important;
  margin-right: 12px !important;
}
</style>
