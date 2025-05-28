let currentTabId = null;
let currentStartTime = null;
let tabHistory = [];

function logInitialTabs() {
  chrome.tabs.query({}, function(tabs) {
    tabs.forEach((tab) => {
      tabHistory.push({
        tabId: tab.id,
        title: tab.title,
        url: tab.url,
        active: tab.active,
        timestamp: new Date().toISOString(),
        initial: true
      });
    });

    chrome.storage.local.set({ tabHistory });
  });
}

function recordTabDuration(tabId, duration) {
  chrome.tabs.get(tabId, (tab) => {
    const record = {
      tabId: tabId,
      title: tab?.title || "Unknown",
      url: tab?.url || "Unknown",
      duration: Math.round(duration / 1000),
      timestamp: new Date().toISOString()
    };

    tabHistory.push(record);
    chrome.storage.local.set({ tabHistory });
  });
}

// 初始化记录
logInitialTabs();

// 切换 tab 时记录前一个 tab 的停留时长
chrome.tabs.onActivated.addListener(activeInfo => {
  const now = Date.now();

  if (currentTabId !== null && currentStartTime !== null) {
    const duration = now - currentStartTime;
    recordTabDuration(currentTabId, duration);
  }

  currentTabId = activeInfo.tabId;
  currentStartTime = now;
});

// 切换窗口时记录离开时间
chrome.windows.onFocusChanged.addListener(windowId => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    if (currentTabId !== null && currentStartTime !== null) {
      const now = Date.now();
      const duration = now - currentStartTime;
      recordTabDuration(currentTabId, duration);
    }

    currentTabId = null;
    currentStartTime = null;
  }
});