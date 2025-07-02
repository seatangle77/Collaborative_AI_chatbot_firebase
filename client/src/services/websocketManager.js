import { ref } from 'vue';

let ws = null;
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
  if (ws) {
    ws.close();
  }

  setStatus('reconnecting');
  ws = new WebSocket(`${WS_BASE_URL}/ws/${groupId}`);

  ws.onopen = () => {
    console.log('🔌 WebSocket connected');
    setStatus('connected');
    reconnectAttempts = 0;
    reconnectDelay = 1000;
    startTimeoutCheck();
  };

  ws.onclose = () => {
    console.log('❌ WebSocket disconnected');
    stopTimeoutCheck();
    tryReconnect(groupId);
  };

  ws.onerror = (error) => {
    console.error('⚠️ WebSocket error:', error);
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
    if (Date.now() - lastMessageTime > 2 * 60 * 1000) { // 2分钟无消息
      console.warn('⏰ WebSocket 超时，主动断开并重连');
      if (ws) ws.close();
    }
  }, 30000); // 每30秒检测一次
}

function stopTimeoutCheck() {
  if (timeoutCheckTimer) {
    clearInterval(timeoutCheckTimer);
    timeoutCheckTimer = null;
  }
}

export function closeWebSocket() {
  if (ws) {
    ws.close();
    ws = null;
  }
  stopTimeoutCheck();
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
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
