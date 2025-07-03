import { ref } from 'vue';

let ws = null;
let wsStatus = 'closed'; // 新增内部状态，防止重复连接
let isManualClose = false; // 新增标志，区分主动关闭和被动断开
const listeners = {};

const WS_BASE_URL = import.meta.env.VITE_WS_BASE || 'wss://collaborative-backend.onrender.com';

// 连接状态：'connected' | 'reconnecting' | 'failed'
export const connectionStatus = ref('reconnecting');

let reconnectAttempts = 0;
let reconnectDelay = 1000; // 初始1秒
const MAX_RECONNECT_ATTEMPTS = 5;
const MAX_RECONNECT_DELAY = 30000; // 30秒
let reconnectTimer = null;

let lastMessageTime = Date.now();
let timeoutCheckTimer = null;

function setStatus(status) {
  connectionStatus.value = status;
}

export function initWebSocket(groupId) {
  // 如果已经连接中或正在连接，直接返回，防止重复连接
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }
  // 如果有旧 ws，且不是已关闭，先关闭
  if (ws && ws.readyState !== WebSocket.CLOSED && ws.readyState !== WebSocket.CLOSING) {
    isManualClose = true; // 标记为主动关闭
    ws.close();
  }
  setStatus('reconnecting');
  ws = new WebSocket(`${WS_BASE_URL}/ws/${groupId}`);
  wsStatus = 'connecting';
  isManualClose = false; // 重置标志

  ws.onopen = () => {
    console.log('🔌 WebSocket connected');
    setStatus('connected');
    wsStatus = 'open';
    reconnectAttempts = 0;
    reconnectDelay = 1000;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    startTimeoutCheck();
  };

  ws.onclose = () => {
    console.log('❌ WebSocket disconnected');
    wsStatus = 'closed';
    stopTimeoutCheck();
    // 只有非主动关闭时才重连
    if (!isManualClose) {
      tryReconnect(groupId);
    }
  };

  ws.onerror = (error) => {
    console.error('⚠️ WebSocket error:', error);
    wsStatus = 'error';
    // 连接出错时，如果是连接阶段就重连，如果是已连接就关闭后重连
    if (ws.readyState === WebSocket.CONNECTING) {
      // 连接阶段出错，直接重连
      tryReconnect(groupId);
    } else if (ws.readyState === WebSocket.OPEN) {
      // 已连接状态出错，主动关闭（会触发 onclose 重连）
      isManualClose = true;
      ws.close();
    }
  };

  ws.onmessage = (event) => {
    lastMessageTime = Date.now();
    try {
      const data = JSON.parse(event.data);
      const type = data.type || data.event;
      const payload = data.payload ?? data;
      console.log('📨 WebSocket 收到消息:', type, payload);
      if (listeners[type]) {
        listeners[type].forEach((cb) => cb(payload));
      }
    } catch (err) {
      console.error('⚠️ Failed to parse WebSocket message:', event.data);
    }
  };
}

function tryReconnect(groupId) {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    setStatus('failed');
    return;
  }
  setStatus('reconnecting');
  reconnectAttempts++;
  reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
  reconnectTimer = setTimeout(() => {
    initWebSocket(groupId);
  }, reconnectDelay);
}

function startTimeoutCheck() {
  stopTimeoutCheck();
  timeoutCheckTimer = setInterval(() => {
    if (Date.now() - lastMessageTime > 7 * 60 * 1000) { // 7分钟无消息
      console.warn('⏰ WebSocket 超时，主动断开并重连');
      if (ws) ws.close();
    }
  }, 60000); // 每1分钟检测一次
}

function stopTimeoutCheck() {
  if (timeoutCheckTimer) {
    clearInterval(timeoutCheckTimer);
    timeoutCheckTimer = null;
  }
}

export function closeWebSocket() {
  isManualClose = true; // 标记为主动关闭
  if (ws) {
    ws.close();
    ws = null;
  }
  stopTimeoutCheck();
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  setStatus('failed'); // 主动关闭时设置为失败状态
}

export function onMessage(type, callback) {
  if (!listeners[type]) {
    listeners[type] = [];
  }
  listeners[type].push(callback);
}

export function removeListeners(type) {
  if (type) {
    listeners[type] = [];
  } else {
    Object.keys(listeners).forEach((key) => {
      listeners[key] = [];
    });
  }
}
