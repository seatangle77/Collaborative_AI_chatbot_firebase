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
          <div v-if="selectedTable === 'anomaly_analysis_results'" style="margin-bottom: 12px;">
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
              <el-table-column prop="id" label="ID" min-width="180px" />
              <el-table-column prop="created_at" label="分析时间" />
              <el-table-column prop="result" label="结果" />
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
            
            <el-table-column v-if="showDelete" label="操作" width="80">
              <template #default="scope">
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
            <el-table-column label="操作" width="80">
              <template #default="scope">
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
  { label: "异常分析结果", value: "anomaly_analysis_results" },
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
    { prop: "id", label: "ID", minWidth: "180px" },
    { prop: "created_at", label: "分析时间" },
    { prop: "result", label: "结果" },
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
const showDelete = computed(() => selectedTable.value === "anomaly_analysis_results");

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
      res = await api.getAnomalyAnalysisResultsByGroup(selectedGroupId.value, page.value, pageSize.value);
      tableData.value = (res.data || []).map(item => ({
        ...item,
        created_at: formatToCST(item.created_at),
        result: item.summary || "",
      }));
      total.value = res.total || 0;
      totalPages.value = res.total_pages || 0;
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
  await api.deleteAnomalyAnalysisResult(id);
  tableData.value = tableData.value.filter(item => item.id !== id);
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
  const ids = multipleSelection.value.map(item => item.id);
  await api.batchDeleteAnomalyAnalysisResults(ids);
  await fetchTableData();
  multipleSelection.value = [];
}

const htmlDialogVisible = ref(false);
const htmlDialogContent = ref("");
function showHtmlDialog(html) {
  htmlDialogContent.value = html;
  htmlDialogVisible.value = true;
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
</style>
