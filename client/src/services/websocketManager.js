let ws = null;
const listeners = {};

export function initWebSocket(groupId) {
  if (ws) {
    ws.close();
  }

  ws = new WebSocket(`ws://localhost:8000/ws/${groupId}`);

  ws.onopen = () => {
    console.log("🔌 WebSocket connected");
  };

  ws.onclose = () => {
    console.log("❌ WebSocket disconnected");
  };

  ws.onerror = (error) => {
    console.error("⚠️ WebSocket error:", error);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      const type = data.type || data.event; // 兼容后端使用 "event" 字段
      const payload = data.payload ?? data; // 如果没有 payload，就使用整个 data

      console.log("📨 WebSocket 收到消息:", type, payload);

      if (listeners[type]) {
        listeners[type].forEach((cb) => cb(payload));
      }
    } catch (err) {
      console.error("⚠️ Failed to parse WebSocket message:", event.data);
    }
  };
}

export function closeWebSocket() {
  if (ws) {
    ws.close();
    ws = null;
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
