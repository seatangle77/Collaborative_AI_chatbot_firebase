<template>
  <div class="admin-page">
    <header>
      <GroupHeader
        v-if="group"
        :group="group"
        :members="filteredMembers"
        :goal="sessionName"
        :session-id="selectedSessionId"
        :session-title="selectedSessionTitle"
        :all-groups="groups"
        :selected-group-id="selectedGroupId"

        @update-group="selectGroup"
      />
    </header>
    <div class="content-container">
      <main class="main-content">
        <div style="width:100%">
          <el-tabs v-model="selectedTable" @tab-click="handleTabClick" style="margin-bottom: 1rem;">
            <el-tab-pane
              v-for="item in tableOptions"
              :key="item.value"
              :label="item.label"
              :name="item.value"
            />
          </el-tabs>
          <div v-if="selectedTable === 'anomaly_analysis_results' || selectedTable === 'local_analyze_history'" style="margin-bottom: 12px;">
            <el-button type="danger" :disabled="!multipleSelection.length" @click="handleBatchDelete">批量删除</el-button>
          </div>
          <div v-if="selectedTable === 'pageBehaviorLogs' && members.length" style="margin-bottom: 12px;">
            <el-tabs v-model="selectedBehaviorUserId" @tab-click="fetchBehaviorLogs">
              <el-tab-pane
                v-for="member in members"
                :key="member.user_id"
                :label="member.name || member.username || member.nickname || member.user_id"
                :name="member.user_id"
              />
            </el-tabs>
          </div>
          <div v-if="selectedTable === 'note_edit_history' && members.length" style="margin-bottom: 12px;">
            <el-tabs v-model="selectedEditUserId" @tab-click="fetchEditHistory">
              <el-tab-pane
                v-for="member in members"
                :key="member.user_id"
                :label="member.name || member.username || member.nickname || member.user_id"
                :name="member.user_id"
              />
            </el-tabs>
          </div>
          <div v-if="selectedTable === 'note_contents' && members.length" style="margin-bottom: 12px;">
            <el-tabs v-model="selectedContentUserId" @tab-click="fetchNoteContents">
              <el-tab-pane
                v-for="member in members"
                :key="member.user_id"
                :label="member.name || member.username || member.nickname || member.user_id"
                :name="member.user_id"
              />
            </el-tabs>
          </div>
          <div v-if="selectedTable === 'feedback_clicks' && members.length" style="margin-bottom: 12px;">
            <el-tabs v-model="selectedFeedbackUserId" @tab-click="fetchFeedbackClicks">
              <el-tab-pane
                v-for="member in members"
                :key="member.user_id"
                :label="member.name || member.username || member.nickname || member.user_id"
                :name="member.user_id"
              />
            </el-tabs>
          </div>
          <div v-if="selectedTable === 'peer_prompts' && members.length" style="margin-bottom: 12px;">
            <el-tabs v-model="selectedPeerPromptUserId" @tab-click="fetchPeerPrompts">
              <el-tab-pane
                v-for="member in members"
                :key="member.user_id"
                :label="member.name || member.username || member.nickname || member.user_id"
                :name="member.user_id"
              />
            </el-tabs>
          </div>
          <el-table
            :data="pagedTableData"
            style="width: 100%"
            v-loading="loading"
            v-if="selectedTable !== 'anomaly_analysis_results'"
          >
            <!-- 异常分析结果列 -->
            <template v-if="selectedTable === 'anomaly_analysis_results'">
              <el-table-column prop="start_time" label="开始时间" width="180" />
              <el-table-column prop="end_time" label="结束时间" width="180" />
              <el-table-column prop="group_type" label="组类型" width="100">
                <template #default="scope">
                  <el-tag :type="getGroupTypeTagType(scope.row.group_type)">
                    {{ scope.row.group_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="group_risk" label="组风险" min-width="200">
                <template #default="scope">
                  <span class="ellipsis" @click="showHtmlDialog(scope.row.group_risk)">
                    {{ scope.row.group_risk && scope.row.group_risk.length > 50 ? scope.row.group_risk.slice(0, 50) + '...' : scope.row.group_risk }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="action_hint" label="行动提示" min-width="200">
                <template #default="scope">
                  <span class="ellipsis" @click="showHtmlDialog(scope.row.action_hint)">
                    {{ scope.row.action_hint && scope.row.action_hint.length > 50 ? scope.row.action_hint.slice(0, 50) + '...' : scope.row.action_hint }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="participation_summary" label="参与情况" min-width="150">
                <template #default="scope">
                  <span class="ellipsis" @click="showParticipationDetails(scope.row)">
                    {{ getParticipationSummary(scope.row) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 本地分析历史列 -->
            <template v-if="selectedTable === 'local_analyze_history'">
              <el-table-column prop="created_at" label="创建时间" width="180" />
              <el-table-column prop="group_id" label="组ID" width="180" />
              <el-table-column prop="user_count" label="用户数" width="80">
                <template #default="scope">
                  <el-tag type="info">{{ scope.row.user_count }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="avg_score" label="平均评分" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.avg_score >= 0.5 ? 'success' : scope.row.avg_score >= 0.3 ? 'warning' : 'danger'">
                    {{ scope.row.avg_score.toFixed(2) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="详情" width="100">
                <template #default="scope">
                  <el-button type="primary" size="small" @click="showLocalAnalyzeDetails(scope.row)">查看详情</el-button>
                </template>
              </el-table-column>
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 语音转写列 -->
            <template v-if="selectedTable === 'speech_transcripts'">
              <el-table-column prop="user_id" label="用户ID" />
              <el-table-column prop="speaker" label="说话人" />
              <el-table-column prop="text" label="转写内容" />
              <el-table-column prop="start" label="开始时间" />
              <el-table-column prop="end" label="结束时间" />
              <el-table-column prop="duration" label="时长(秒)" />
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 页面行为日志列 -->
            <template v-if="selectedTable === 'pageBehaviorLogs'">
              <el-table-column prop="userId" label="用户ID" />
              <el-table-column prop="userName" label="用户名" />
              <el-table-column prop="windowStart" label="开始时间" />
              <el-table-column prop="windowEnd" label="结束时间" />
              <el-table-column prop="activeTabTitle" label="活跃标签页标题" />
              <el-table-column prop="activeTabUrl" label="活跃标签页URL" />
              <el-table-column prop="activeTabTime" label="活跃标签页时间" />
              <el-table-column prop="tabHistoryCount" label="标签历史数" />
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 笔记编辑历史列 -->
            <template v-if="selectedTable === 'note_edit_history'">
              <el-table-column prop="userId" label="用户ID" />
              <el-table-column prop="updatedAt" label="更新时间" />
              <el-table-column prop="summary" label="摘要" />
              <el-table-column prop="charCount" label="字符数" />
              <el-table-column prop="isDelete" label="是否删除" />
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 笔记内容列 -->
            <template v-if="selectedTable === 'note_contents'">
              <el-table-column prop="userId" label="用户ID" />
              <el-table-column prop="updatedAt" label="更新时间" />
              <el-table-column prop="noteId" label="noteId" />
              <el-table-column prop="html" label="HTML内容" min-width="180px">
                <template #default="scope">
                  <span class="ellipsis" @click="showHtmlDialog(scope.row.html)">
                    {{ scope.row.html && scope.row.html.length > 30 ? scope.row.html.slice(0, 30) + '...' : scope.row.html }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 反馈点击记录列 -->
            <template v-if="selectedTable === 'feedback_clicks'">
              <el-table-column prop="click_type" label="点击类型" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.click_type === 'More' ? 'success' : scope.row.click_type === 'Less' ? 'danger' : 'warning'">
                    {{ scope.row.click_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="clicked_at" label="点击时间" width="180" />
              <el-table-column prop="detail_type" label="详情类型" width="120" />
              <el-table-column prop="detail_status" label="详情状态" min-width="300">
                <template #default="scope">
                  <span class="ellipsis" @click="showHtmlDialog(scope.row.detail_status)">
                    {{ scope.row.detail_status && scope.row.detail_status.length > 80 ? scope.row.detail_status.slice(0, 80) + '...' : scope.row.detail_status }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <!-- 同伴提示记录列 -->
            <template v-if="selectedTable === 'peer_prompts'">
              <el-table-column prop="content" label="提示内容" min-width="300">
                <template #default="scope">
                  <span class="ellipsis" @click="showHtmlDialog(scope.row.content)">
                    {{ scope.row.content && scope.row.content.length > 100 ? scope.row.content.slice(0, 100) + '...' : scope.row.content }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="180" />
              <el-table-column prop="to_user_id" label="接收用户ID" width="180" />
              <el-table-column prop="push_sent" label="推送状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.push_sent ? 'success' : 'warning'">
                    {{ scope.row.push_sent ? '已推送' : '未推送' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="push_sent_at" label="推送时间" width="180" />
              <el-table-column prop="id" label="ID" min-width="180px" />
            </template>
            
            <el-table-column v-if="showDelete" label="操作" width="150">
              <template #default="scope">
                <el-button type="primary" size="small" @click="showRecordDetails(scope.row)" style="margin-right: 5px;">详情</el-button>
                <el-button type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-table
            v-else
            :data="pagedTableData"
            style="width: 100%"
            v-loading="loading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column v-for="col in columns" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.minWidth || '120px'" />
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="primary" size="small" @click="showRecordDetails(scope.row)" style="margin-right: 5px;">详情</el-button>
                <el-button type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-if="total > pageSize"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
            style="margin-top: 1rem;"
          />
          <el-dialog v-model="htmlDialogVisible" title="HTML内容预览" width="60%">
            <div v-html="htmlDialogContent" style="max-height:60vh;overflow:auto;"></div>
          </el-dialog>
          
          <!-- 异常分析结果详情弹窗 -->
          <el-dialog v-model="recordDetailsVisible" title="异常分析结果详情" width="80%" :close-on-click-modal="false">
            <div v-if="currentRecordDetails" class="record-details">
              <!-- 基本信息 -->
              <div class="detail-section">
                <h3>基本信息</h3>
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-label">记录ID：</span>
                    <span class="info-value">{{ currentRecordDetails.id }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">开始时间：</span>
                    <span class="info-value">{{ currentRecordDetails.start_time }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">结束时间：</span>
                    <span class="info-value">{{ currentRecordDetails.end_time }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">创建时间：</span>
                    <span class="info-value">{{ formatToCST(currentRecordDetails.created_at) }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">组ID：</span>
                    <span class="info-value">{{ currentRecordDetails.group_id }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 组级别分析 -->
              <div class="detail-section">
                <h3>组级别分析</h3>
                <div class="group-analysis">
                  <div class="analysis-item">
                    <span class="analysis-label">组类型：</span>
                    <el-tag :type="getGroupTypeTagType(currentRecordDetails.group_type)">
                      {{ currentRecordDetails.group_type }}
                    </el-tag>
                  </div>
                  <div class="analysis-item">
                    <span class="analysis-label">组风险：</span>
                    <span class="analysis-value">{{ currentRecordDetails.group_risk }}</span>
                  </div>
                  <div class="analysis-item">
                    <span class="analysis-label">行动提示：</span>
                    <span class="analysis-value">{{ currentRecordDetails.action_hint }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 用户分析详情 -->
              <div class="detail-section">
                <h3>用户分析详情</h3>
                <div class="user-analysis-list">
                  <div 
                    v-for="(userData, userId) in currentRecordDetails.raw_response" 
                    :key="userId" 
                    class="user-analysis-item"
                  >
                    <div class="user-header">
                      <h4>{{ userData.user_name || userId }}</h4>
                      <el-tag :type="getUserTypeTagType(userData.detail?.type)">
                        {{ userData.detail?.type || '未知' }}
                      </el-tag>
                    </div>
                    
                    <div class="user-content">
                      <div class="user-summary">
                        <span class="summary-label">摘要：</span>
                        <span class="summary-content">{{ userData.summary }}</span>
                      </div>
                      
                      <div class="user-detail">
                        <div class="detail-row">
                          <span class="detail-label">状态：</span>
                          <span class="detail-value">{{ userData.detail?.status }}</span>
                        </div>
                        <div class="detail-row">
                          <span class="detail-label">建议：</span>
                          <span class="detail-value">{{ userData.detail?.suggestion }}</span>
                        </div>
                        <div class="detail-row">
                          <span class="detail-label">眼镜提示：</span>
                          <span class="detail-value">{{ userData.glasses_summary }}</span>
                        </div>
                      </div>
                      
                      <div class="user-evidence">
                        <span class="evidence-label">证据：</span>
                        <div class="evidence-content" v-html="formatEvidence(userData.detail?.evidence)"></div>
                      </div>
                      
                      <div class="user-more-info" v-if="userData.more_info">
                        <div class="more-info-item">
                          <span class="more-info-label">详细原因：</span>
                          <span class="more-info-content">{{ userData.more_info.detailed_reason }}</span>
                        </div>
                        <div class="more-info-item">
                          <span class="more-info-label">协作建议：</span>
                          <span class="more-info-content">{{ userData.more_info.collaboration_suggestion }}</span>
                        </div>
                        <div class="more-info-item">
                          <span class="more-info-label">组内对比：</span>
                          <span class="more-info-content">{{ userData.more_info.group_comparison }}</span>
                        </div>
                        <div class="more-info-item">
                          <span class="more-info-label">历史对比：</span>
                          <span class="more-info-content">{{ userData.more_info.history_comparison }}</span>
                        </div>
                        <div class="more-info-item">
                          <span class="more-info-label">额外数据：</span>
                          <span class="more-info-content">{{ userData.more_info.extra_data }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-dialog>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watchEffect, watch } from "vue";
import api from "../services/apiService";
import GroupHeader from "@/components/admin/GroupHeader.vue";
import StageTimeline from "@/components/admin/StageTimeline.vue";
import SpeechLogPanel from "@/components/admin/SpeechLogPanel.vue";
import BehaviorLogPanel from "@/components/admin/BehaviorLogPanel.vue";
import dayjs from "dayjs";

const group = ref(null);
const session = ref(null);
const agenda = ref({ items: [] });
const bot = ref(null);
const members = ref([]);
const users = ref({});
const groups = ref([]);
const selectedGroupId = ref(null);

const speechData = ref([]);
const behaviorData = ref([]);

const currentStage = ref(-1);

function handleStageSelect(index) {
  currentStage.value = index;
}

const currentTask = computed(() => {
  return agenda.value.items?.[currentStage.value]?.task || "";
});

const currentDescription = computed(() => {
  return agenda.value.items?.[currentStage.value]?.agenda_description || "";
});

const allocatedTime = computed(() => {
  return agenda.value.items?.[currentStage.value]?.allocated_time_minutes || 0;
});

const selectGroup = async (groupId) => {
  selectedGroupId.value = groupId;
  const groupData = groups.value.find((g) => g.id === groupId);
  if (!groupData) return;

  group.value = groupData;

  const userList = await api.getUsers();
  users.value = userList.reduce((acc, user) => {
    acc[user.user_id] = user;
    return acc;
  }, {});

  const memberList = await api.getGroupMembers(groupId);
  members.value = memberList.map((m) => users.value[m.user_id]).filter(Boolean);

  await fetchTableData();
};



const selectedSessionId = computed(() => session.value?.id || "");
const selectedSessionTitle = computed(() => session.value?.session_title || "");
const sessionName = computed(() => group.value?.group_goal || "");
const filteredMembers = computed(() =>
  members.value.map((m) => users.value[m.user_id] || m).filter(Boolean)
);

// ====== 数据表切换相关 ======
const selectedTable = ref("anomaly_analysis_results");
const tableOptions = [
  { label: "AI分析结果", value: "anomaly_analysis_results" },
  { label: "本地分析历史", value: "local_analyze_history" },
  { label: "语音转写", value: "speech_transcripts" },
  { label: "页面行为日志", value: "pageBehaviorLogs" },
  { label: "笔记编辑历史", value: "note_edit_history" },
  { label: "笔记内容", value: "note_contents" },
  { label: "反馈点击记录", value: "feedback_clicks" },
  { label: "同伴提示记录", value: "peer_prompts" },
];
const tableData = ref([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(20);
// 新增分页相关变量
const total = ref(0);
const totalPages = ref(0);

const columnsMap = {
  note_edit_history: [
    { prop: "userId", label: "用户ID" },
    { prop: "updatedAt", label: "更新时间" },
    { prop: "summary", label: "摘要" },
    { prop: "charCount", label: "字符数" },
    { prop: "isDelete", label: "是否删除" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  note_contents: [
    { prop: "userId", label: "用户ID" },
    { prop: "updatedAt", label: "更新时间" },
    { prop: "noteId", label: "noteId" },
    { prop: "html", label: "HTML内容" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  pageBehaviorLogs: [
    { prop: "userId", label: "用户ID" },
    { prop: "userName", label: "用户名" },
    { prop: "windowStart", label: "开始时间" },
    { prop: "windowEnd", label: "结束时间" },
    { prop: "activeTabTitle", label: "活跃标签页标题" },
    { prop: "activeTabUrl", label: "活跃标签页URL" },
    { prop: "activeTabTime", label: "活跃标签页时间" },
    { prop: "tabHistoryCount", label: "标签历史数" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  speech_transcripts: [
    { prop: "user_id", label: "用户ID" },
    { prop: "speaker", label: "说话人" },
    { prop: "text", label: "转写内容" },
    { prop: "start", label: "开始时间" },
    { prop: "end", label: "结束时间" },
    { prop: "duration", label: "时长(秒)" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  anomaly_analysis_results: [
    { prop: "start_time", label: "开始时间", minWidth: "180px" },
    { prop: "end_time", label: "结束时间", minWidth: "180px" },
    { prop: "user_count", label: "用户数", minWidth: "80px" },
    { prop: "group_type", label: "组类型", minWidth: "100px" },
    { prop: "group_risk", label: "组风险", minWidth: "200px" },
    { prop: "action_hint", label: "行动提示", minWidth: "200px" },
    { prop: "participation_summary", label: "参与情况", minWidth: "150px" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  local_analyze_history: [
    { prop: "created_at", label: "创建时间", minWidth: "180px" },
    { prop: "group_id", label: "组ID", minWidth: "180px" },
    { prop: "user_count", label: "用户数", minWidth: "80px" },
    { prop: "avg_score", label: "平均评分", minWidth: "100px" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  feedback_clicks: [
    { prop: "click_type", label: "点击类型" },
    { prop: "clicked_at", label: "点击时间" },
    { prop: "detail_type", label: "详情类型" },
    { prop: "detail_status", label: "详情状态" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
  peer_prompts: [
    { prop: "content", label: "提示内容" },
    { prop: "created_at", label: "创建时间" },
    { prop: "to_user_id", label: "接收用户ID" },
    { prop: "push_sent", label: "推送状态" },
    { prop: "push_sent_at", label: "推送时间" },
    { prop: "id", label: "ID", minWidth: "180px" },
  ],
};
const columns = computed(() => {
  const cols = columnsMap[selectedTable.value] || [];
  return cols.filter(col => col && typeof col === 'object' && col.prop);
});
const showDelete = computed(() => selectedTable.value === "anomaly_analysis_results" || selectedTable.value === "local_analyze_history");

const pagedTableData = computed(() => {
  return tableData.value;
});

function formatToCST(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

function formatToCSTForSpeech(utcStr) {
  if (!utcStr) return "";
  // 如果没有Z或+00:00，强制加Z
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(utcStr)) {
    utcStr += "Z";
  }
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

function formatToCSTForBehavior(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

const selectedBehaviorUserId = ref("");

watch(members, (val) => {
  if (val && val.length) {
    selectedBehaviorUserId.value = val[0].user_id;
  }
});

async function fetchBehaviorLogs() {
  if (!selectedBehaviorUserId.value) {
    tableData.value = [];
    total.value = 0;
    totalPages.value = 0;
    return;
  }
  page.value = 1; // 重置页码
  loading.value = true;
  const res = await api.getPageBehaviorLogsByUser(selectedBehaviorUserId.value, page.value, pageSize.value);
  tableData.value = (res.data || []).map(item => ({
    ...item,
    userName: item.behaviorData?.user?.userName || "",
    windowStart: formatToCSTForBehavior(item.windowStart),
    windowEnd: formatToCSTForBehavior(item.windowEnd),
    activeTabTitle: item.behaviorData?.activeTab?.title || "",
    activeTabUrl: item.behaviorData?.activeTab?.url || "",
    activeTabTime: formatToCSTForBehavior(item.behaviorData?.activeTab?.timestamp),
    tabHistoryCount: item.behaviorData?.tabHistory?.length || 0,
  }));
  total.value = res.total || 0;
  totalPages.value = res.total_pages || 0;
  loading.value = false;
}

const selectedEditUserId = ref("");

watch(members, (val) => {
  if (val && val.length) {
    selectedEditUserId.value = val[0].user_id;
  }
});

function formatToCSTForEdit(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

async function fetchEditHistory() {
  if (!selectedEditUserId.value) {
    tableData.value = [];
    total.value = 0;
    totalPages.value = 0;
    return;
  }
  page.value = 1; // 重置页码
  loading.value = true;
  const res = await api.getNoteEditHistoryByUser(selectedEditUserId.value, page.value, pageSize.value);
  tableData.value = (res.data || []).map(item => ({
    ...item,
    updatedAt: formatToCSTForEdit(item.updatedAt),
  }));
  total.value = res.total || 0;
  totalPages.value = res.total_pages || 0;
  loading.value = false;
}

const selectedContentUserId = ref("");

watch(members, (val) => {
  if (val && val.length) {
    selectedContentUserId.value = val[0].user_id;
  }
});

const selectedFeedbackUserId = ref("");

watch(members, (val) => {
  if (val && val.length) {
    selectedFeedbackUserId.value = val[0].user_id;
  }
});

const selectedPeerPromptUserId = ref("");

watch(members, (val) => {
  if (val && val.length) {
    selectedPeerPromptUserId.value = val[0].user_id;
  }
});

function formatToCSTForContent(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

async function fetchNoteContents() {
  if (!selectedContentUserId.value) {
    tableData.value = [];
    total.value = 0;
    totalPages.value = 0;
    return;
  }
  page.value = 1; // 重置页码
  loading.value = true;
  const res = await api.getNoteContentsByUser(selectedContentUserId.value, page.value, pageSize.value);
  tableData.value = (res.data || []).map(item => ({
    ...item,
    userId: item.user_id || item.userId || "",
    updatedAt: formatToCSTForContent(item.updated_at || item.updatedAt),
    noteId: item.note_id || item.noteId || "",
    html: item.html || "",
  }));
  total.value = res.total || 0;
  totalPages.value = res.total_pages || 0;
  loading.value = false;
}

function formatToCSTForFeedback(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

async function fetchFeedbackClicks() {
  if (!selectedFeedbackUserId.value) {
    tableData.value = [];
    total.value = 0;
    totalPages.value = 0;
    return;
  }
  page.value = 1; // 重置页码
  loading.value = true;
  const res = await api.getFeedbackClicksByUser(selectedFeedbackUserId.value, page.value, pageSize.value);
  tableData.value = (res.data || []).map(item => ({
    ...item,
    clicked_at: formatToCSTForFeedback(item.clicked_at),
  }));
  total.value = res.total || 0;
  totalPages.value = res.total_pages || 0;
  loading.value = false;
}

function formatToCSTForPeerPrompt(utcStr) {
  if (!utcStr) return "";
  return dayjs(utcStr).format("YYYY-MM-DD HH:mm:ss");
}

async function fetchPeerPrompts() {
  if (!selectedPeerPromptUserId.value) {
    tableData.value = [];
    total.value = 0;
    totalPages.value = 0;
    return;
  }
  page.value = 1; // 重置页码
  loading.value = true;
  const res = await api.getPeerPromptsByUser(selectedPeerPromptUserId.value, page.value, pageSize.value);
  tableData.value = (res.data || []).map(item => ({
    ...item,
    created_at: formatToCSTForPeerPrompt(item.created_at),
    push_sent_at: formatToCSTForPeerPrompt(item.push_sent_at),
  }));
  total.value = res.total || 0;
  totalPages.value = res.total_pages || 0;
  loading.value = false;
}

async function fetchTableData() {
  if (!selectedGroupId.value) return;
  loading.value = true;
  let res = [];
  switch (selectedTable.value) {
    case "note_edit_history":
      await fetchEditHistory();
      loading.value = false;
      return;
    case "note_contents":
      await fetchNoteContents();
      loading.value = false;
      return;
    case "pageBehaviorLogs":
      await fetchBehaviorLogs();
      loading.value = false;
      return;
    case "feedback_clicks":
      await fetchFeedbackClicks();
      loading.value = false;
      return;
    case "peer_prompts":
      await fetchPeerPrompts();
      loading.value = false;
      return;
    case "speech_transcripts":
      res = await api.getSpeechTranscriptsByGroup(selectedGroupId.value, page.value, pageSize.value);
      tableData.value = (res.data || []).map(item => ({
        ...item,
        start: formatToCSTForSpeech(item.start),
        end: formatToCSTForSpeech(item.end),
        duration: item.duration ? Number(item.duration).toFixed(2) : "",
      }));
      total.value = res.total || 0;
      totalPages.value = res.total_pages || 0;
      break;
    case "anomaly_analysis_results":
      try {
        res = await api.getAnomalyAnalysisGroupResultsByGroup(selectedGroupId.value, page.value, pageSize.value);
        tableData.value = (res.data || []).map(item => {
          const rawResponse = item.raw_response || {};
          
          // 获取第一个用户的 group_distribution 信息（所有用户应该相同）
          const firstUserId = Object.keys(rawResponse)[0];
          const firstUserData = rawResponse[firstUserId] || {};
          const groupDistribution = firstUserData.group_distribution || {};
          
          // 统计用户参与情况
          const userCounts = {
            high: 0,
            low: 0,
            normal: 0,
            no: 0,
            total: Object.keys(rawResponse).length
          };
          
          // 遍历所有用户，统计参与类型
          Object.values(rawResponse).forEach(userData => {
            if (userData.detail && userData.detail.type) {
              const type = userData.detail.type;
              if (type === 'High Participation') userCounts.high++;
              else if (type === 'Low Participation') userCounts.low++;
              else if (type === 'Normal Participation') userCounts.normal++;
              else if (type === 'No Participation') userCounts.no++;
            }
          });
          
          return {
            ...item,
            start_time: formatToCST(item.start_time),
            end_time: formatToCST(item.end_time),
            group_type: groupDistribution.group_type || "",
            group_risk: groupDistribution.group_risk || "",
            action_hint: groupDistribution.action_hint || "",
            participation_summary: `${userCounts.high}高/${userCounts.low}低/${userCounts.normal}正常/${userCounts.no}无参与`,
            user_count: userCounts.total,
            // 保存原始数据用于详情显示
            raw_response: rawResponse,
          };
        });
        total.value = res.total || 0;
        totalPages.value = res.total_pages || 0;
      } catch (error) {
        console.error("获取异常分析结果失败:", error);
        tableData.value = [];
        total.value = 0;
        totalPages.value = 0;
      }
      break;
    case "local_analyze_history":
      try {
        res = await api.getLocalAnalyzeHistoryByGroup(selectedGroupId.value, page.value, pageSize.value);
        tableData.value = (res.data || []).map(item => {
          const output = item.output || {};
          const anomalyHistory = output.anomaly_history || [];
          const localAnalysisResult = output.local_analysis_result || {};
          const timeRange = output.time_range || {};
          const noteEditHistory = output.raw_tables?.note_edit_history || [];
          const users = output.users || [];
          
          // 计算平均评分
          let totalScore = 0;
          let scoreCount = 0;
          
          // 遍历用户分析结果，计算平均评分
          Object.values(localAnalysisResult).forEach(userData => {
            if (userData.total_score !== undefined && userData.total_score !== null) {
              totalScore += userData.total_score;
              scoreCount++;
            }
          });
          
          const avgScore = scoreCount > 0 ? totalScore / scoreCount : 0;
          
          return {
            ...item,
            created_at: formatToCST(item.created_at),
            user_count: Object.keys(localAnalysisResult).length,
            avg_score: avgScore,
            // 保存原始数据用于详情显示
            output: output,
          };
        });
        total.value = res.total || 0;
        totalPages.value = res.total_pages || 0;
      } catch (error) {
        console.error("获取本地分析历史失败:", error);
        tableData.value = [];
        total.value = 0;
        totalPages.value = 0;
      }
      break;
  }
  loading.value = false;
}

function handlePageChange(val) {
  page.value = val;
  fetchTableData();
}

function handleSizeChange(val) {
  pageSize.value = val;
  page.value = 1; // 当每页条数改变时，重置当前页为1
  fetchTableData();
}

async function handleDelete(id) {
  try {
    if (selectedTable.value === "anomaly_analysis_results") {
      await api.deleteAnomalyAnalysisGroupResult(id);
    } else if (selectedTable.value === "local_analyze_history") {
      await api.deleteLocalAnalyzeHistory(id);
    } else {
      await api.deleteAnomalyAnalysisResult(id);
    }
    tableData.value = tableData.value.filter(item => item.id !== id);
  } catch (error) {
    console.error("删除失败:", error);
  }
}

watch([selectedGroupId, selectedTable], () => {
  page.value = 1; // 重置页码
  fetchTableData();
});

onMounted(async () => {
  groups.value = await api.getGroups();
  if (!groups.value.length) return;

  const defaultGroupId = groups.value[0].id;
  await selectGroup(defaultGroupId);
  await fetchTableData();
});

// 调试输出 agenda.value.items 变化
watchEffect(() => {
  console.log(
    "📋 agenda.value.items from parent (AdminPage):",
    agenda.value.items
  );
});

// 统一处理 agenda 数据传递
const agendaItems = computed(() => agenda.value.items || []);

function handleTabClick() {
  // watch(selectedTable) 已自动处理数据刷新，这里可留空
}

const multipleSelection = ref([]);

function handleSelectionChange(val) {
  multipleSelection.value = val;
}

async function handleBatchDelete() {
  if (!multipleSelection.value.length) return;
  try {
    const ids = multipleSelection.value.map(item => item.id);
    if (selectedTable.value === "anomaly_analysis_results") {
      await api.batchDeleteAnomalyAnalysisGroupResults(ids);
    } else if (selectedTable.value === "local_analyze_history") {
      await api.batchDeleteLocalAnalyzeHistory(ids);
    } else {
      await api.batchDeleteAnomalyAnalysisResults(ids);
    }
    await fetchTableData();
    multipleSelection.value = [];
  } catch (error) {
    console.error("批量删除失败:", error);
  }
}

const htmlDialogVisible = ref(false);
const htmlDialogContent = ref("");

// 异常分析结果详情相关
const recordDetailsVisible = ref(false);
const currentRecordDetails = ref(null);
function showHtmlDialog(html) {
  htmlDialogContent.value = html;
  htmlDialogVisible.value = true;
}

// 显示记录详情
function showRecordDetails(record) {
  currentRecordDetails.value = record;
  recordDetailsVisible.value = true;
}

// 获取用户类型标签颜色
function getUserTypeTagType(userType) {
  switch (userType) {
    case "High Participation":
      return "success";
    case "Low Participation":
      return "warning";
    case "No Participation":
      return "danger";
    case "Normal Participation":
      return "info";
    default:
      return "info";
  }
}

// 格式化证据内容
function formatEvidence(evidence) {
  if (!evidence) return "";
  return evidence.replace(/\n/g, "<br/>");
}

// 获取组类型标签颜色
function getGroupTypeTagType(groupType) {
  switch (groupType) {
    case "失衡型":
      return "danger";
    case "均衡型":
      return "success";
    case "活跃型":
      return "warning";
    default:
      return "info";
  }
}

// 获取参与情况摘要
function getParticipationSummary(item) {
  // 从 raw_response 中获取 group_distribution
  const groupDistribution = item.raw_response?.group_distribution || item.group_distribution;
  
  if (!groupDistribution) return "无数据";
  
  const { high = 0, low = 0, normal = 0, no = 0 } = groupDistribution;
  const total = high + low + normal + no;
  if (total === 0) return "无参与数据";
  
  return `高参与:${high} 低参与:${low} 正常:${normal} 无参与:${no}`;
}

// 显示参与详情
function showParticipationDetails(item) {
  const rawResponse = item.raw_response || {};
  
  if (!rawResponse || Object.keys(rawResponse).length === 0) {
    showHtmlDialog("无参与数据");
    return;
  }
  
  // 获取第一个用户的 group_distribution 信息
  const firstUserId = Object.keys(rawResponse)[0];
  const firstUserData = rawResponse[firstUserId] || {};
  const groupDistribution = firstUserData.group_distribution || {};
  
  // 统计用户参与情况
  const userCounts = {
    high: 0,
    low: 0,
    normal: 0,
    no: 0,
    dominant: groupDistribution.dominant || 0
  };
  
  // 构建用户详情信息
  let userDetails = "";
  
  // 遍历所有用户数据
  Object.entries(rawResponse).forEach(([userId, userData]) => {
    const detail = userData.detail || {};
    const moreInfo = userData.more_info || {};
    
    // 统计参与类型
    if (detail.type) {
      if (detail.type === 'High Participation') userCounts.high++;
      else if (detail.type === 'Low Participation') userCounts.low++;
      else if (detail.type === 'Normal Participation') userCounts.normal++;
      else if (detail.type === 'No Participation') userCounts.no++;
    }
    
    userDetails += `
      <div style="margin: 10px 0; padding: 10px; border: 1px solid #eee; border-radius: 5px; background: #f9f9f9;">
        <h5 style="color: #3478f6; margin: 0 0 8px 0;">用户: ${userData.user_name || userId}</h5>
        <p><strong>参与类型：</strong><span style="color: #e67e22; font-weight: 600;">${detail.type || "未知"}</span></p>
        <p><strong>状态：</strong>${detail.status || "未知"}</p>
        <p><strong>建议：</strong>${detail.suggestion || "无"}</p>
        <p><strong>摘要：</strong>${userData.summary || "无"}</p>
        <p><strong>眼镜提示：</strong>${userData.glasses_summary || "无"}</p>
        <p><strong>详细原因：</strong>${moreInfo.detailed_reason || "无"}</p>
        <p><strong>协作建议：</strong>${moreInfo.collaboration_suggestion || "无"}</p>
        <p><strong>组内对比：</strong>${moreInfo.group_comparison || "无"}</p>
      </div>
    `;
  });
  
  const details = `
    <h4>参与情况详情</h4>
    <p><strong>高参与成员：</strong>${userCounts.high}人</p>
    <p><strong>低参与成员：</strong>${userCounts.low}人</p>
    <p><strong>正常参与成员：</strong>${userCounts.normal}人</p>
    <p><strong>无参与成员：</strong>${userCounts.no}人</p>
    <p><strong>主导者：</strong>${userCounts.dominant}人</p>
    <hr>
    <h4>组风险</h4>
    <p>${groupDistribution.group_risk || "无"}</p>
    <h4>行动提示</h4>
    <p>${groupDistribution.action_hint || "无"}</p>
    <hr>
    <h4>用户详情</h4>
    ${userDetails || "无用户详情"}
  `;
  
  showHtmlDialog(details);
}

// 显示本地分析详情
function showLocalAnalyzeDetails(item) {
  const output = item.output || {};
  const localAnalysisResult = output.local_analysis_result || {};
  const timeRange = output.time_range || {};
  
  // 构建基本信息
  let basicInfo = `
    <h4>基本信息</h4>
    <p><strong>记录ID：</strong>${item.id}</p>
    <p><strong>创建时间：</strong>${item.created_at}</p>
    <p><strong>组ID：</strong>${item.group_id}</p>
    <p><strong>分析时间范围：</strong>${formatToCST(timeRange.start)} ~ ${formatToCST(timeRange.end)}</p>
    <p><strong>用户总数：</strong>${Object.keys(localAnalysisResult).length}人</p>
  `;
  
  // 构建用户分析详情
  let userAnalysisDetails = "";
  Object.entries(localAnalysisResult).forEach(([userId, userData]) => {
    const userName = userData.name || userId;
    const totalLevel = userData.total_level || "未知";
    const totalScore = userData.total_score || 0;
    
    // 根据参与度设置颜色
    let levelColor = "#666";
    if (totalLevel.includes('High')) levelColor = "#52c41a";
    else if (totalLevel.includes('Low')) levelColor = "#faad14";
    else if (totalLevel.includes('No')) levelColor = "#f5222d";
    
    userAnalysisDetails += `
      <div style="margin: 15px 0; padding: 15px; border: 1px solid #e4e7ed; border-radius: 8px; background: #fafbfc;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 2px solid #3478f6; padding-bottom: 8px;">
          <h5 style="color: #3478f6; margin: 0; font-size: 16px;">用户: ${userName}</h5>
          <div style="display: flex; gap: 10px; align-items: center;">
            <span style="color: ${levelColor}; font-weight: 600; font-size: 14px;">${totalLevel}</span>
            <el-tag :type="${totalScore >= 0.5 ? 'success' : totalScore >= 0.3 ? 'warning' : 'danger'}" style="margin-left: 8px;">${totalScore.toFixed(2)}</el-tag>
          </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
          <div style="background: #f0f6ff; padding: 12px; border-radius: 6px; border-left: 4px solid #3478f6;">
            <h6 style="color: #3478f6; margin: 0 0 8px 0; font-size: 14px;">发言行为</h6>
            <p style="margin: 4px 0;"><strong>等级：</strong>${userData.speech_level || "未知"}</p>
            <p style="margin: 4px 0;"><strong>时长：</strong>${userData.speech_duration || "0s"}</p>
            <p style="margin: 4px 0;"><strong>占比：</strong>${userData.speech_percent || "0%"}</p>
            <p style="margin: 4px 0;"><strong>评分：</strong>${userData.speech_level_score || 0}</p>
          </div>
          <div style="background: #fff7e6; padding: 12px; border-radius: 6px; border-left: 4px solid #faad14;">
            <h6 style="color: #faad14; margin: 0 0 8px 0; font-size: 14px;">编辑行为</h6>
            <p style="margin: 4px 0;"><strong>等级：</strong>${userData.note_edit_level || "未知"}</p>
            <p style="margin: 4px 0;"><strong>次数：</strong>${userData.note_edit_count || 0}</p>
            <p style="margin: 4px 0;"><strong>字符数：</strong>${userData.note_edit_char_count || 0}</p>
            <p style="margin: 4px 0;"><strong>评分：</strong>${userData.note_edit_score || 0}</p>
          </div>
          <div style="background: #f6ffed; padding: 12px; border-radius: 6px; border-left: 4px solid #52c41a;">
            <h6 style="color: #52c41a; margin: 0 0 8px 0; font-size: 14px;">浏览行为</h6>
            <p style="margin: 4px 0;"><strong>等级：</strong>${userData.browser_level || "未知"}</p>
            <p style="margin: 4px 0;"><strong>页面数：</strong>${userData.page_count || 0}</p>
            <p style="margin: 4px 0;"><strong>评分：</strong>${userData.browser_score || 0}</p>
          </div>
          <div style="background: #fff2f0; padding: 12px; border-radius: 6px; border-left: 4px solid #ff4d4f;">
            <h6 style="color: #ff4d4f; margin: 0 0 8px 0; font-size: 14px;">鼠标操作</h6>
            <p style="margin: 4px 0;"><strong>次数：</strong>${userData.mouse_action_count || 0}</p>
            <p style="margin: 4px 0;"><strong>时长：</strong>${userData.mouse_duration || "0s"}</p>
            <p style="margin: 4px 0;"><strong>占比：</strong>${userData.mouse_percent || "0%"}</p>
          </div>
        </div>
      </div>
    `;
  });
  
  const details = `
    ${basicInfo}
    <hr>
    <h4>用户参与度分析详情 (${Object.keys(localAnalysisResult).length}个用户)</h4>
    ${userAnalysisDetails || "无用户分析数据"}
  `;
  
  showHtmlDialog(details);
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100vw;
  margin: 0 auto;
  box-sizing: border-box;
}

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

main.main-content {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  flex: 1;
  padding: 24px 32px;
}

.speech-panel,
.behavior-panel {
  width: 50%;
  min-height: 700px;
  font-size: 16px;
}

.ellipsis {
  display: inline-block;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  color: #409EFF;
}

/* 异常分析结果详情样式 */
.record-details {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafbfc;
}

.detail-section h3 {
  margin: 0 0 16px 0;
  color: #3478f6;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 2px solid #3478f6;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
  margin-right: 8px;
}

.info-value {
  color: #333;
  font-family: monospace;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.group-analysis {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.analysis-label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
  margin-top: 4px;
}

.analysis-value {
  color: #333;
  line-height: 1.6;
  flex: 1;
}

.user-analysis-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-analysis-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  overflow: hidden;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f0f6ff;
  border-bottom: 1px solid #e4e7ed;
}

.user-header h4 {
  margin: 0;
  color: #3478f6;
  font-size: 16px;
  font-weight: 600;
}

.user-content {
  padding: 16px;
}

.user-summary {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #3478f6;
}

.summary-label {
  font-weight: 600;
  color: #3478f6;
  margin-right: 8px;
}

.summary-content {
  color: #333;
  font-weight: 500;
}

.user-detail {
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
  align-items: flex-start;
}

.detail-label {
  font-weight: 600;
  color: #666;
  min-width: 80px;
  margin-right: 8px;
  margin-top: 2px;
}

.detail-value {
  color: #333;
  flex: 1;
  line-height: 1.5;
}

.user-evidence {
  margin-bottom: 16px;
  padding: 12px;
  background: #fffbe6;
  border-radius: 6px;
  border-left: 4px solid #e6a23c;
}

.evidence-label {
  font-weight: 600;
  color: #b26a00;
  display: block;
  margin-bottom: 8px;
}

.evidence-content {
  color: #b26a00;
  line-height: 1.6;
  font-size: 13px;
}

.user-more-info {
  background: #f9f9f9;
  border-radius: 6px;
  padding: 12px;
}

.more-info-item {
  margin-bottom: 12px;
}

.more-info-item:last-child {
  margin-bottom: 0;
}

.more-info-label {
  font-weight: 600;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

.more-info-content {
  color: #333;
  line-height: 1.6;
  font-size: 13px;
}
</style>
