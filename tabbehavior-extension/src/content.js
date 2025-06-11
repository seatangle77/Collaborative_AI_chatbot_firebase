// 加载调试标记
console.log("[TabBehavior] content.js loaded");

const messageThrottle = {
  click: 0,
  keydown: 0,
  scroll: 0,
  mousemove: 0,
  focus_input: 0,
  visibility: 0,
  inactivity_check: 0,
};
const THROTTLE_INTERVAL = 500; // 500ms节流

function safeSendMessage(msg, retries = 3, delay = 200) {
  function attempt(remaining) {
    try {
      chrome.runtime.sendMessage(msg, (response) => {
        if (chrome.runtime.lastError && remaining > 0) {
          setTimeout(() => attempt(remaining - 1), delay);
        }
      });
    } catch (e) {
      if (remaining > 0) {
        setTimeout(() => attempt(remaining - 1), delay);
      }
    }
  }
  attempt(retries);
}

let isCollecting = true;
// 页面加载时自动添加事件监听
addEventListeners();

console.log("[TabBehavior] content.js 默认开启采集");

// 通知 background 注入成功
try {
  safeSendMessage({
    type: "contentScriptLoaded",
    url: window.location.href,
    timestamp: Date.now()
  });
} catch (e) {
  console.warn("[TabBehavior] sendMessage failed:", e);
}

// 初始化交互统计变量
let clickCount = 0;
let keydownCount = 0;
let scrollDepth = 0;
let hasScrolled = false;
let focusInput = false;

// 事件处理函数
function clickHandler(e) {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.click < THROTTLE_INTERVAL) return;
  messageThrottle.click = now;

  clickCount++;
  const clickPosition = { x: e.clientX, y: e.clientY };
  const msg = {
    type: "click",
    count: clickCount,
    position: clickPosition,
    timestamp: now
  };
  console.log("[TabBehavior] Sent:", msg);
  try {
    safeSendMessage(msg);
  } catch (e) {
    console.warn("[TabBehavior] sendMessage failed:", e);
  }
}

function keydownHandler(e) {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.keydown < THROTTLE_INTERVAL) return;
  messageThrottle.keydown = now;

  keydownCount++;
  const msg = {
    type: "keydown",
    count: keydownCount,
    timestamp: now
  };
  console.log("[TabBehavior] Sent:", msg);
  try {
    safeSendMessage(msg);
  } catch (e) {
    console.warn("[TabBehavior] sendMessage failed:", e);
  }
}

function scrollHandler(e) {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.scroll < THROTTLE_INTERVAL) return;
  messageThrottle.scroll = now;

  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const currentDepth = docHeight > 0 ? (scrollTop / docHeight) : 0;
  if (currentDepth > scrollDepth) {
    scrollDepth = currentDepth;
  }
  hasScrolled = true;
  const msg = {
    type: "scroll",
    maxDepth: scrollDepth,
    timestamp: now
  };
  console.log("[TabBehavior] Sent:", msg);
  try {
    safeSendMessage(msg);
  } catch (e) {
    console.warn("[TabBehavior] sendMessage failed:", e);
  }
}

let lastMouseMoveTime = 0;
function mousemoveHandler(e) {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.mousemove < THROTTLE_INTERVAL) return;
  messageThrottle.mousemove = now;

  if (now - lastMouseMoveTime > 500) {
    lastMouseMoveTime = now;
    const msg = {
      type: "mousemove",
      position: { x: e.clientX, y: e.clientY },
      timestamp: now
    };
    console.log("[TabBehavior] Sent:", msg);
    try {
      safeSendMessage(msg);
    } catch (e) {
      console.warn("[TabBehavior] sendMessage failed:", e);
    }
  }
}

function focusinHandler(e) {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.focus_input < THROTTLE_INTERVAL) return;
  messageThrottle.focus_input = now;

  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable) {
    focusInput = true;
    const msg = {
      type: "focus_input",
      value: true,
      timestamp: now
    };
    console.log("[TabBehavior] Sent:", msg);
    try {
      safeSendMessage(msg);
    } catch (e) {
      console.warn("[TabBehavior] sendMessage failed:", e);
    }
  }
}

function visibilityChangeHandler() {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.visibility < THROTTLE_INTERVAL) return;
  messageThrottle.visibility = now;

  const msg = {
    type: "visibility",
    visible: document.visibilityState === "visible",
    timestamp: now
  };
  console.log("[TabBehavior] Sent:", msg);
  try {
    safeSendMessage(msg);
  } catch (e) {
    console.warn("[TabBehavior] sendMessage failed:", e);
  }
}

// 封装事件监听注册和注销
function addEventListeners() {
  document.addEventListener("click", clickHandler);
  document.addEventListener("keydown", keydownHandler);
  document.addEventListener("scroll", scrollHandler);
  document.addEventListener("mousemove", mousemoveHandler);
  document.addEventListener("focusin", focusinHandler);
  document.addEventListener("visibilitychange", visibilityChangeHandler);
}

function removeEventListeners() {
  document.removeEventListener("click", clickHandler);
  document.removeEventListener("keydown", keydownHandler);
  document.removeEventListener("scroll", scrollHandler);
  document.removeEventListener("mousemove", mousemoveHandler);
  document.removeEventListener("focusin", focusinHandler);
  document.removeEventListener("visibilitychange", visibilityChangeHandler);
}

// 无操作持续时间逻辑
let inactivityStart = Date.now();
let lastActiveTime = Date.now();
let inactivityTimer = setInterval(() => {
  if (!isCollecting) return;
  const now = Date.now();
  if (now - messageThrottle.inactivity_check < THROTTLE_INTERVAL) return;
  messageThrottle.inactivity_check = now;

  const idleDuration = now - lastActiveTime;
  const msg = {
    type: "inactivity_check",
    idleMs: idleDuration,
    lastActive: lastActiveTime
  };
  console.log("[TabBehavior] Sent:", msg);
  try {
    safeSendMessage(msg);
  } catch (e) {
    console.warn("[TabBehavior] sendMessage failed:", e);
  }
}, 10000); // 每 10 秒报告一次无操作时间

// 重置最后活跃时间的事件列表
["click", "scroll", "keydown", "mousemove"].forEach((eventType) => {
  document.addEventListener(eventType, () => {
    if (!isCollecting) return;
    lastActiveTime = Date.now();
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("[TabBehavior] content.js 收到消息:", message);

  // 移除对 control start/stop 消息的响应，默认采集始终开启
  // if (message.type === "control") {
  //   sendResponse({ status: "ok" });
  //   return true;
  // }
  sendResponse({ status: "ok" });
});


window.addEventListener("beforeunload", () => {
  if (isCollecting) {
    removeEventListeners();
    isCollecting = false;
    console.log("[TabBehavior] content.js 页面卸载，停止采集");
  }
});
// 监听 window 的 message 事件，转发用户信息消息到 background
window.addEventListener("message", (event) => {
  if (event.source !== window) return;
  const message = event.data;
  if (message && message.type === "user_data_update") {
    const userInfo = message.payload;
    console.log("[TabBehavior content.js] 收到用户信息:", userInfo);
    chrome.runtime.sendMessage({
      type: "user_data_update",
      payload: userInfo,
    });
  }
});