<template>
  <div class="popup-container">
    <h2 class="title">TabBehavior 插件</h2>

    <el-card class="info-card">
      <p>
        <strong>👤 当前用户：</strong> {{ currentUser.userName || "加载中..." }}
      </p>
    </el-card>

    <el-card class="info-card">
      <p><strong>当前标签页：</strong> {{ activeTab?.title || "加载中..." }}</p>
      <p><strong>URL：</strong> {{ activeTab?.url || "未知" }}</p>
    </el-card>

    <el-card class="info-card" v-if="tabHistory.length > 0">
      <h3>📊 历史记录</h3>
      <div class="scrollable">
        <el-table :data="tabHistory" style="width: 100%" size="small">
          <el-table-column prop="title" label="标题" min-width="120" />
          <el-table-column prop="url" label="链接" min-width="150" />
          <el-table-column prop="duration" label="停留 (s)" width="80" />
          <el-table-column
            prop="timestamp"
            label="时间"
            min-width="140"
            :formatter="formatTime"
          />
        </el-table>
      </div>

      <template v-if="Object.keys(tabDurations).length > 0">
        <h4 style="margin-top: 12px">📘 每个 Tab 的停留记录：</h4>
        <ul>
          <li v-for="(durations, tabId) in tabDurations" :key="tabId">
            Tab {{ tabId }}：{{ durations.join("s, ") }}s
          </li>
        </ul>
      </template>
    </el-card>

    <el-card
      class="info-card"
      v-if="pageInsights || tabBehaviorLogs.length > 0"
    >
      <h3>🧠 综合行为数据</h3>
      <div v-if="pageInsights">
        <p><strong>页面域名：</strong> {{ pageInsights.domain }}</p>
        <p>
          <strong>页面加载时间：</strong>
          {{ formatTime(null, null, pageInsights.loadTimestamp) }}
        </p>
        <p>
          <strong>最近活跃时间：</strong>
          {{ formatTime(null, null, pageInsights.lastActive) }}
        </p>
        <p>
          <strong>无操作时长：</strong>
          {{ Math.round(pageInsights.idleMs / 1000) }} 秒
        </p>
      </div>

      <div v-if="tabBehaviorLogs.length > 0">
        <div class="scrollable">
          <el-table
            :data="tabBehaviorLogs"
            style="width: 100%; margin-top: 8px"
            size="small"
          >
            <el-table-column prop="type" label="事件类型" width="100" />
            <el-table-column
              prop="timestamp"
              label="时间"
              min-width="140"
              :formatter="formatTime"
            />
            <el-table-column
              prop="position"
              label="位置/内容"
              min-width="140"
              :formatter="formatDetail"
            />
          </el-table>
        </div>
      </div>

      <div class="scrollable" style="margin-top: 12px">
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

    <el-card class="info-card" v-if="Object.keys(injectedSites).length > 0">
      <h3>🧩 Content 脚本注入情况</h3>
      <ul>
        <li v-for="(info, domain) in injectedSites" :key="domain">
          <strong>{{ domain }}</strong> - 注入成功于
          {{ formatTime(null, null, info.timestamp) }}
        </li>
      </ul>
    </el-card>

    <el-card
      class="info-card"
      style="max-height: 300px; overflow-y: auto; margin-top: 16px"
    >
      <h3>📅 最近 60 秒行为数据</h3>
      <pre
        style="font-size: 12px; white-space: pre-wrap; word-break: break-all"
        >{{ last30sJson }}</pre
      >
    </el-card>

    <el-button type="primary" style="margin-top: 12px" @click="openDetailPage">
      查看详情
    </el-button>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from "vue";
import { ElCard, ElButton, ElTable, ElTableColumn } from "element-plus";

const currentUser = ref({});
const activeTab = ref(null);
const tabHistory = ref([]);
const tabDurations = ref({});
const pageInsights = ref(null);
const injectedSites = ref({});
const tabBehaviorLogs = ref([]);

chrome.storage.local.get(["tabBehaviorLogs"], (res) => {
  tabBehaviorLogs.value = res.tabBehaviorLogs || [];
});

function safeSendMessage(msg) {
  if (document.visibilityState !== "visible") {
    console.warn("[TabBehavior] 页面不可见，跳过发送消息");
    return;
  }
  try {
    chrome.runtime.sendMessage(msg, (response) => {
      if (chrome.runtime.lastError) {
        console.warn(
          "[TabBehavior] sendMessage失败:",
          chrome.runtime.lastError.message
        );
      } else {
        console.log("[TabBehavior] sendMessage成功:", response);
      }
    });
  } catch (e) {
    console.warn("[TabBehavior] sendMessage异常:", e);
  }
}

const refreshTabs = () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];
    if (!currentTab) {
      console.warn("[TabBehavior] 当前标签页不存在，可能已关闭");
      activeTab.value = null;
      return;
    }
    chrome.tabs.get(currentTab.id, (tab) => {
      if (chrome.runtime.lastError) {
        console.warn(
          "[TabBehavior] 无法获取当前标签页：",
          chrome.runtime.lastError.message
        );
        activeTab.value = null;
        return;
      }
      activeTab.value = tab;
    });
  });

  chrome.storage.local.get(["tabHistory"], (res) => {
    tabHistory.value = res.tabHistory || [];

    // 构建 tabId → 停留时间数组映射
    const durationsMap = {};
    for (const record of tabHistory.value) {
      if (record.duration && record.tabId != null) {
        if (!durationsMap[record.tabId]) durationsMap[record.tabId] = [];
        durationsMap[record.tabId].push(record.duration);
      }
    }
    tabDurations.value = durationsMap;
  });

  chrome.storage.local.get(["pageInsights"], (res) => {
    pageInsights.value = res.pageInsights || null;
  });

  chrome.storage.local.get(["contentInjectionLogs"], (res) => {
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
      } catch (_) {
        // 忽略非法 URL
      }
    }
    injectedSites.value = grouped;
  });

  chrome.storage.local.get(["tabBehaviorLogs"], (res) => {
    tabBehaviorLogs.value = res.tabBehaviorLogs || [];
  });
};

const formatTime = (_, __, cellValue) => {
  const d = new Date(cellValue);
  return d.toLocaleString();
};

const formatDetail = (row) => {
  if (row.position) {
    return `x: ${row.position.x}, y: ${row.position.y}`;
  }
  if (row.detail) return row.detail;
  return "-";
};

const behaviorJSON = computed(() => {
  return JSON.stringify(
    {
      tabHistory: tabHistory.value,
      activeTab: activeTab.value,
      tabBehaviorLogs: tabBehaviorLogs.value,
    },
    null,
    2
  );
});

function openDetailPage() {
  chrome.tabs.create({ url: chrome.runtime.getURL("src/detail/index.html") });
}

const last30sJson = ref("{}");

function fetchLast30sData() {
  chrome.storage.local.get(["tabBehaviorLogs"], (res) => {
    const logs = res.tabBehaviorLogs || [];
    const windowStart = Date.now() - 30 * 1000;
    const recentLogs = logs.filter((item) => {
      return new Date(item.timestamp).getTime() >= windowStart;
    });
    last30sJson.value = JSON.stringify(recentLogs, null, 2);
  });
}

let intervalId = null;

onMounted(() => {
  chrome.storage.local.get(["pluginData"], (res) => {
    currentUser.value = res.pluginData?.user || {};
  });
  refreshTabs();
  fetchLast30sData();
  intervalId = setInterval(fetchLast30sData, 30000);
});

onBeforeUnmount(() => {
  clearInterval(intervalId);
});
</script>

<style scoped>
.popup-container {
  padding: 16px;
  width: 360px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  background-color: #f9f9f9;
}

.title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.info-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  max-height: 250px;
  overflow: hidden;
}
.scrollable {
  flex: 1;
  overflow-y: auto;
}

.actions {
  display: flex;
  justify-content: flex-end;
}
</style>
