import { ref } from 'vue';

let ws = null;
let listeners = {};
export const userWsStatus = ref('closed');

export function connectUserWebSocket(userId) {
    if (ws) {
        ws.close();
        ws = null;
    }
    ws = new WebSocket(`${import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'}/ws/user/${userId}`);
    ws.onopen = () => {
        userWsStatus.value = 'connected';
        console.log('[userWs] 已连接');
    };
    ws.onclose = () => {
        userWsStatus.value = 'closed';
        console.log('[userWs] 已关闭');
    };
    ws.onerror = (e) => {
        userWsStatus.value = 'error';
        console.error('[userWs] 连接出错', e);
    };
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('[userWs] 收到消息:', data);
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
    if (ws) {
        ws.close();
        ws = null;
    }
    listeners = {};
    userWsStatus.value = 'closed';
} 