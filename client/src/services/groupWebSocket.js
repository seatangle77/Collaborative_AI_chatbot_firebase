let ws = null;
let listeners = {};

export function connectGroupWebSocket(groupId) {
    if (ws) {
        ws.close();
        ws = null;
    }
    ws = new WebSocket(`${import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'}/ws/${groupId}`);
    ws.onopen = () => console.log('[groupWs] 已连接');
    ws.onclose = () => console.log('[groupWs] 已关闭');
    ws.onerror = (e) => console.error('[groupWs] 连接出错', e);
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('[groupWs] 收到消息:', data);
            if (data.type && listeners[data.type]) {
                listeners[data.type].forEach(cb => cb(data));
            }
        } catch (err) {
            console.error('❌ group ws 消息解析失败:', err, event.data);
        }
    };
}

export function onGroupMessage(type, callback) {
    if (!listeners[type]) listeners[type] = [];
    listeners[type].push(callback);
}

export function closeGroupWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
    listeners = {};
} 