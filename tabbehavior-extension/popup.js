// 获取当前用户名（模拟或从 storage 中获取）
chrome.storage.local.get(["username"], (result) => {
  const username = result.username || "Emma";
  document.getElementById("username").innerText = username;
});

function renderTabHistory() {
  chrome.storage.local.get(["tabHistory"], (result) => {
    const tabHistory = result.tabHistory || [];
    const listEl = document.getElementById("tabList");
    listEl.innerHTML = ""; // 清空默认内容

    tabHistory.forEach(record => {
      const item = document.createElement("li");
      item.className = record.initial ? "initial" : "duration";
      if (record.initial) {
        item.innerText = `[初始] ${record.title} - ${record.url}`;
      } else {
        item.innerText = `[停留 ${record.duration}s] TabID: ${record.tabId}`;
      }
      listEl.appendChild(item);
    });

    if (tabHistory.length === 0) {
      listEl.innerHTML = "<li>无记录</li>";
    }

    // 构建每个 tabId 的停留历史数组
    const pageHistoryEl = document.getElementById("pageHistoryList");
    const tabVisitMap = {};

    tabHistory.forEach(record => {
      if (!record.initial && record.tabId && record.duration) {
        if (!tabVisitMap[record.tabId]) {
          tabVisitMap[record.tabId] = [];
        }
        tabVisitMap[record.tabId].push(record.duration);
      }
    });

    pageHistoryEl.innerHTML = ""; // 清空历史

    Object.entries(tabVisitMap).forEach(([tabId, durations]) => {
      const li = document.createElement("li");
      li.innerText = `TabID ${tabId} 的停留记录：${JSON.stringify(durations)} (共 ${durations.length} 次)`;
      pageHistoryEl.appendChild(li);
    });
  });
}

// 初始渲染
renderTabHistory();

// 刷新按钮逻辑
document.getElementById("refreshBtn").onclick = () => {
  renderTabHistory();
};

// =========================
// 模拟数据：David 和 Frank 的标签页内容
function renderMockUserTabs() {
  const davidTabs = [
    {
      tabId: 1001,
      duration: 35,
      timestamp: new Date().toISOString()
    },
    {
      tabId: 1001,
      duration: 50,
      timestamp: new Date().toISOString()
    },
    {
      tabId: 1002,
      title: "Reddit: Are AI writing assistants helping or hurting students?",
      url: "https://www.reddit.com/r/college/comments/ai_writing_tools/",
      timestamp: new Date().toISOString(),
      initial: true
    },
    {
      tabId: 1002,
      duration: 22,
      timestamp: new Date().toISOString()
    }
  ];

  const frankTabs = [
    {
      tabId: 2001,
      title: "AI in Education: Opportunities and Risks",
      url: "https://edtechfuture.org/ai-impact-on-university-students",
      timestamp: new Date().toISOString(),
      initial: true
    },
    {
      tabId: 2001,
      duration: 40,
      timestamp: new Date().toISOString()
    },
    {
      tabId: 2001,
      duration: 32,
      timestamp: new Date().toISOString()
    },
    {
      tabId: 2002,
      title: "YouTube - Debate: Should AI Tools Be Allowed in Assignments?",
      url: "https://www.youtube.com/watch?v=ai-tools-discussion",
      timestamp: new Date().toISOString(),
      initial: true
    },
    {
      tabId: 2002,
      duration: 15,
      timestamp: new Date().toISOString()
    }
  ];

  const davidList = document.getElementById("davidTabs");
  const frankList = document.getElementById("frankTabs");

  davidList.innerHTML = "";
  frankList.innerHTML = "";

  const renderList = (data, container) => {
    data.forEach(record => {
      const item = document.createElement("li");
      item.className = record.initial ? "initial" : "duration";
      if (record.initial) {
        item.innerText = `[初始] ${record.title} - ${record.url}`;
      } else {
        item.innerText = `[停留 ${record.duration}s] TabID: ${record.tabId}`;
      }
      container.appendChild(item);
    });
  };

  renderList(davidTabs, davidList);
  renderList(frankTabs, frankList);
}

// 初始化渲染模拟数据
renderMockUserTabs();