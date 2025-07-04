import { ref } from 'vue';

let ws = null;
let listeners = {};
let heartbeatInterval = null;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 8000; // 8秒发送一次心跳，确保长连接稳定
const RECONNECT_DELAY = 3000; // 3秒重连延迟

export const userWsStatus = ref('closed');

function startHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    heartbeatInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'heartbeat',
                timestamp: new Date().toISOString()
            }));
            console.log('[userWs] 💓 发送心跳 (8秒间隔)');
        }
    }, HEARTBEAT_INTERVAL);
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
    }
}

function tryReconnect(userId) {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.log('[userWs] ❌ 重连次数已达上限，停止重连');
        userWsStatus.value = 'failed';
        return;
    }

    reconnectAttempts++;
    console.log(`[userWs] 🔄 第${reconnectAttempts}次重连尝试...`);

    reconnectTimer = setTimeout(() => {
        connectUserWebSocket(userId);
    }, RECONNECT_DELAY);
}

export function connectUserWebSocket(userId) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('[userWs] 已连接，跳过重复连接');
        return;
    }

    if (ws) {
        ws.close();
        ws = null;
    }

    stopHeartbeat();

    const wsUrl = `${import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'}/ws/user/${userId}`;
    console.log(`[userWs] 🔌 连接WebSocket: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        userWsStatus.value = 'connected';
        reconnectAttempts = 0;
        console.log('[userWs] ✅ 连接成功，开始8秒心跳维持');
        startHeartbeat();
    };

    ws.onclose = (event) => {
        userWsStatus.value = 'closed';
        stopHeartbeat();
        console.log('[userWs] ❌ 连接关闭', event.code, event.reason);

        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000) {
            tryReconnect(userId);
        }
    };

    ws.onerror = (e) => {
        userWsStatus.value = 'error';
        console.error('[userWs] ⚠️ 连接出错', e);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('[userWs] 📨 收到消息:', data);

            // 处理心跳响应
            if (data.type === 'heartbeat_ack') {
                console.log('[userWs] 💓 收到心跳响应');
                return;
            }

            // 处理其他消息
            if (data.type && listeners[data.type]) {
                listeners[data.type].forEach(cb => cb(data));
            }
        } catch (err) {
            console.error('❌ user ws 消息解析失败:', err, event.data);
        }
    };
}

export function onUserMessage(type, callback) {
    if (!listeners[type]) listeners[type] = [];
    listeners[type].push(callback);
}

export function closeUserWebSocket() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }

    stopHeartbeat();

    if (ws) {
        ws.close(1000, '主动关闭'); // 1000表示正常关闭
        ws = null;
    }

    listeners = {};
    userWsStatus.value = 'closed';
    reconnectAttempts = 0;

    console.log('[userWs] 🚪 主动关闭连接');
} 