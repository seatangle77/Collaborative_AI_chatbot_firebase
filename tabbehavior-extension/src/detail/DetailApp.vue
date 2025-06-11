<template>
  <el-row
    :gutter="20"
    style="
      padding: 20px;
      min-height: 100vh;
      background: #f5f7fa;
      max-width: 1200px;
      box-sizing: border-box;
      margin: 0 auto;
      overflow-x: auto;
    "
  >
    <el-col :xs="24" :sm="24" :md="10" :lg="10" :xl="10">
      <h2 class="title">TabBehavior 插件</h2>
      <div style="margin-bottom: 12px">
        <span style="margin-left: 12px"
          >当前状态：{{ isCollecting ? "收集中" : "已停止" }}</span
        >
      </div>
      <el-card
        shadow="hover"
        style="margin-bottom: 20px; max-height: 220px; overflow-y: auto"
      >
        <h3>👤 当前用户</h3>
        <p>{{ userName || "加载中..." }}</p>
      </el-card>

      <el-card
        shadow="hover"
        style="margin-bottom: 20px; max-height: 250px; overflow-y: auto"
      >
        <h3>当前标签页</h3>
        <p>标题：{{ activeTab?.title || "加载中..." }}</p>
        <p>URL：{{ activeTab?.url || "未知" }}</p>
      </el-card>

      <el-card
        shadow="hover"
        v-if="Object.keys(injectedSites).length > 0"
        style="max-height: 300px; overflow-y: auto"
      >
        <h3>🧩 Content 脚本注入情况</h3>
        <ul style="padding-left: 20px">
          <li v-for="(info, domain) in injectedSites" :key="domain">
            <strong>{{ domain }}</strong> - 注入成功于
            {{ formatTime(null, null, info.timestamp) }}
          </li>
        </ul>
      </el-card>
    </el-col>

    <!-- 新增 历史时间窗口 JSON 列表 -->
    <el-col
      :xs="24"
      :sm="24"
      :md="24"
      :lg="24"
      :xl="24"
      style="margin-top: 20px"
    >
      <el-card
        shadow="hover"
        style="margin-bottom: 20px; max-height: 400px; overflow-y: auto"
      >
        <h3>🕒 行为 JSON 时间窗口历史</h3>
        <el-table
          :data="behaviorJsonList"
          style="width: 100%"
          size="small"
          max-height="360px"
          height="360"
        >
          <el-table-column prop="windowStart" label="开始时间" min-width="180">
            <template #default="{ row }">
              {{ formatTime(null, null, row.windowStart) }}
            </template>
          </el-table-column>
          <el-table-column prop="tabBehaviorLogs" label="事件数" width="80">
            <template #default="{ row }">
              {{ row.tabBehaviorLogs?.length || 0 }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" @click="openDetail(row)"
                >查看详情</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      <el-dialog
        v-model="detailDialogVisible"
        title="行为 JSON 详情"
        width="600px"
        :close-on-click-modal="false"
      >
        <pre
          style="
            max-height: 400px;
            overflow: auto;
            font-size: 12px;
            background: #f4f4f4;
            padding: 8px;
            white-space: pre-wrap;
            word-break: break-word;
          "
          >{{ selectedJson }}</pre
        >
        <template #footer>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </el-col>

    <el-col :xs="24" :sm="24" :md="14" :lg="14" :xl="14">
      <el-card
        shadow="hover"
        v-if="tabHistory.length > 0"
        style="
          margin-bottom: 20px;
          overflow-x: auto;
          max-height: 400px;
          overflow-y: auto;
        "
      >
        <h3>📊 历史记录</h3>
        <el-table
          :data="tabHistory"
          style="width: 100%"
          size="small"
          max-height="360px"
          height="360"
          class="break-word-table"
        >
          <el-table-column prop="title" label="标题" min-width="150">
            <template #default="{ row }">
              <div class="break-word-cell">{{ row.title }}</div>
            </template>
          </el-table-column>
          <el-table-column label="链接" min-width="250">
            <template #default="{ row }">
              <div class="break-word-cell">{{ row.url }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="停留 (s)" width="90" />
          <el-table-column
            prop="timestamp"
            label="时间"
            min-width="180"
            :formatter="formatTime"
          />
        </el-table>

        <template
          v-if="Object.keys(tabDurations).length > 0"
          style="margin-top: 12px"
        >
          <h4>📘 每个 Tab 的停留记录：</h4>
          <ul style="padding-left: 20px">
            <li v-for="(durations, tabId) in tabDurations" :key="tabId">
              Tab {{ tabId }}：{{ durations.join("s, ") }}s
            </li>
          </ul>
        </template>
      </el-card>

      <el-card
        shadow="hover"
        style="margin-bottom: 20px; max-height: 400px; overflow-y: auto"
      >
        <h3>🧠 综合行为数据</h3>
        <div v-if="pageInsights" style="margin-bottom: 12px">
          <p>页面域名：{{ pageInsights.domain }}</p>
          <p>
            页面加载时间：
            {{ formatTime(null, null, pageInsights.loadTimestamp) }}
          </p>
          <p>
            最近活跃时间：{{ formatTime(null, null, pageInsights.lastActive) }}
          </p>
          <p>无操作时长：{{ Math.round(pageInsights.idleMs / 1000) }} 秒</p>
        </div>

        <el-table
          :data="tabBehaviorLogs"
          style="width: 100%"
          size="small"
          max-height="360px"
          height="360"
          v-if="tabBehaviorLogs.length > 0"
          class="break-word-table"
        >
          <el-table-column prop="type" label="事件类型" width="120" />
          <el-table-column
            prop="timestamp"
            label="时间"
            min-width="180"
            :formatter="formatTime"
          />
          <el-table-column label="位置/内容" min-width="180">
            <template #default="{ row }">
              <div class="break-word-cell">
                {{
                  row.position
                    ? `x: ${row.position.x}, y: ${row.position.y}`
                    : row.detail || "-"
                }}
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top: 12px">
          <p><strong>📦 行为 JSON：</strong></p>
          <pre
            style="
              font-size: 12px;
              max-height: 200px;
              overflow: auto;
              background: #f4f4f4;
              padding: 8px;
            "
            >{{ behaviorJSON }}
          </pre>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from "vue";
import {
  ElRow,
  ElCol,
  ElCard,
  ElTable,
  ElTableColumn,
  ElButton,
  ElDialog,
} from "element-plus";

const userName = ref("");
const activeTab = ref(null);
const tabHistory = ref([]);
const tabDurations = ref({});
const pageInsights = ref(null);
const injectedSites = ref({});
const tabBehaviorLogs = ref([]);

const fullBehaviorLogs = ref([]); // 存储全部日志
const slidingWindowLogs = ref([]); // 滑动窗口内最近60秒日志

let intervalId = null;

const isCollecting = ref(true);

// 存储当前用户完整信息
const currentUser = ref({});

// 表示当前数据时间窗口开始时间
const windowStart = ref(Date.now() - 30000);
// 表示当前数据时间窗口结束时间
const windowEnd = ref(Date.now());

// 新增：历史 JSON 时间窗口列表
const behaviorJsonList = ref([]);
// 新增：详情弹窗控制
const detailDialogVisible = ref(false);
const selectedJson = ref("");

// 删除 startCollecting 和 stopCollecting 函数

// 该函数负责刷新标签页状态及从 chrome.storage 读取数据
const refreshTabs = () => {
  console.log("refreshTabs 开始");

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];
    if (!currentTab) {
      activeTab.value = null;
      return;
    }
    chrome.tabs.get(currentTab.id, (tab) => {
      if (chrome.runtime.lastError) {
        activeTab.value = null;
        return;
      }
      activeTab.value = tab;
    });
  });

  chrome.storage.local.get(
    [
      "tabHistory",
      "pluginData",
      "pageInsights",
      "contentInjectionLogs",
      "tabBehaviorLogs",
    ],
    (res) => {
      console.log("storage读取结果：", res);

      tabHistory.value = res.tabHistory || [];
      userName.value = res.pluginData?.user?.userName || "";
      currentUser.value = res.pluginData?.user || {}; // 新增赋值
      pageInsights.value = res.pageInsights || null;

      console.log("pageInsights:", pageInsights.value);
      console.log("tabBehaviorLogs长度:", (res.tabBehaviorLogs || []).length);

      // 更新全部日志
      fullBehaviorLogs.value = res.tabBehaviorLogs || [];

      // 计算滑动窗口内最近60秒的日志
      refreshSlidingWindow();

      const logs = res.contentInjectionLogs || [];
      const grouped = {};
      for (const log of logs) {
        try {
          const domain = new URL(log.url).hostname;
          if (!grouped[domain]) grouped[domain] = log;
          else if (
            new Date(log.timestamp) > new Date(grouped[domain].timestamp)
          ) {
            grouped[domain] = log;
          }
        } catch (_) {}
      }
      injectedSites.value = grouped;

      const durationsMap = {};
      for (const record of tabHistory.value) {
        if (record.duration && record.tabId != null) {
          if (!durationsMap[record.tabId]) durationsMap[record.tabId] = [];
          durationsMap[record.tabId].push(record.duration);
        }
      }
      tabDurations.value = durationsMap;
    }
  );
};

// 滑动窗口刷新函数，筛选最近30秒数据
// 该函数筛选最近30秒的行为日志
function refreshSlidingWindow() {
  const windowStartTime = Date.now() - 30 * 1000;
  console.log("全部日志:", fullBehaviorLogs.value);
  slidingWindowLogs.value = fullBehaviorLogs.value.filter(
    (item) => new Date(item.timestamp).getTime() >= windowStartTime
  );
  console.log("最近30秒日志:", slidingWindowLogs.value);
}

const formatTime = (_, __, cellValue) => {
  if (!cellValue) return "";
  const d = new Date(cellValue);
  return d.toLocaleString();
};

// 生成包含时间窗口、用户信息及行为数据的JSON字符串
const behaviorJSON = computed(() => {
  return JSON.stringify(
    {
      tabHistory: tabHistory.value,
      activeTab: activeTab.value,
      tabBehaviorLogs: slidingWindowLogs.value,
      user: currentUser.value, // 新增 user 字段
      windowStart: new Date(windowStart.value).toISOString(),
      windowEnd: new Date(windowEnd.value).toISOString(),
    },
    null,
    2
  );
});

// 新增：推入新的行为 JSON 到 behaviorJsonList
function pushNewBehaviorJson(newJson) {
  behaviorJsonList.value.unshift(newJson);
  // 保持列表不超过20条
  if (behaviorJsonList.value.length > 20) {
    behaviorJsonList.value.length = 20;
  }
}

// 新增：打开详情弹窗
function openDetail(row) {
  selectedJson.value = JSON.stringify(row, null, 2);
  detailDialogVisible.value = true;
}

function handleStorageChange(changes, areaName) {
  if (areaName === "local") {
    refreshTabs();
  }
}

onMounted(() => {
  // 询问后台当前采集状态，初始化按钮状态
  chrome.runtime.sendMessage({ type: "queryStatus" }, (response) => {
    if (response?.status === "started") {
      isCollecting.value = true;
    } else {
      isCollecting.value = false;
    }
  });

  refreshTabs();

  // 每30秒刷新滑动窗口日志
  intervalId = setInterval(() => {
    // 先刷新全部日志，再刷新滑动窗口
    chrome.storage.local.get(
      [
        "tabHistory",
        "pluginData",
        "pageInsights",
        "contentInjectionLogs",
        "tabBehaviorLogs",
      ],
      (res) => {
        // 更新核心变量
        tabHistory.value = res.tabHistory || [];
        userName.value = res.pluginData?.user?.userName || "";
        currentUser.value = res.pluginData?.user || {};
        fullBehaviorLogs.value = res.tabBehaviorLogs || [];
        // 更新时间窗口
        windowEnd.value = Date.now();
        windowStart.value = windowEnd.value - 30000;
        refreshSlidingWindow();
        // 构建窗口 JSON
        const windowJson = {
          tabHistory: tabHistory.value,
          activeTab: activeTab.value,
          tabBehaviorLogs: slidingWindowLogs.value,
          user: currentUser.value,
          windowStart: new Date(windowStart.value).toISOString(),
          windowEnd: new Date(windowEnd.value).toISOString(),
        };
        pushNewBehaviorJson(windowJson);
      }
    );
  }, 30 * 1000);

  chrome.storage.onChanged.addListener(handleStorageChange);
});

onBeforeUnmount(() => {
  chrome.storage.onChanged.removeListener(handleStorageChange);
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped>
.popup-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
}

.title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
  padding: 16px;
}

/* 新增表格内文本换行样式 */
.break-word-table .break-word-cell {
  white-space: normal !important;
  word-break: break-word !important;
}

/* 控制表格最小宽度和横向滚动 */
.el-table {
  min-width: 700px !important;
  overflow-x: auto !important;
}

/* JSON 区域自动换行，限制高度 */
pre {
  max-height: 300px !important;
  overflow: auto !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  background: #f4f4f4;
  padding: 8px;
  font-size: 12px;
}

/* 所有卡片最大宽度不超出视口 */
.el-card {
  max-width: 100vw !important;
  box-sizing: border-box;
  background-color: #ffffff !important; /* 设置背景为白色 */
  padding: 10px !important;
}

/* 页整体宽度 */
.el-row {
  max-width: 100vw !important;
  overflow-x: hidden;
}
</style>
