// 群组 WebSocket 统一管理器
// 支持多群组并发连接、消息分发、连接状态管理和自动重连

const groupSockets = {};
const listeners = {};
const status = {};
const reconnectTimers = {};
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY = 1000;

const WS_BASE_URL = import.meta.env.VITE_WS_BASE || 'wss://collaborative-backend.onrender.com';

function getSocketUrl(groupId) {
    return `${WS_BASE_URL}/ws/${groupId}`;
}

export function connectGroupSocket(groupId) {
    if (groupSockets[groupId] && groupSockets[groupId].readyState === WebSocket.OPEN) {
        return;
    }
    if (groupSockets[groupId]) {
        groupSockets[groupId].close();
        groupSockets[groupId] = null;
    }
    status[groupId] = 'connecting';
    let attempts = 0;
    function doConnect() {
        const socket = new WebSocket(getSocketUrl(groupId));
        groupSockets[groupId] = socket;
        status[groupId] = 'connecting';
        socket.onopen = () => {
            status[groupId] = 'open';
            attempts = 0;
            if (reconnectTimers[groupId]) {
                clearTimeout(reconnectTimers[groupId]);
                reconnectTimers[groupId] = null;
            }
        };
        socket.onclose = () => {
            status[groupId] = 'closed';
            if (attempts < MAX_RECONNECT_ATTEMPTS) {
                attempts++;
                const delay = RECONNECT_BASE_DELAY * Math.pow(2, attempts);
                reconnectTimers[groupId] = setTimeout(doConnect, delay);
            }
        };
        socket.onerror = (e) => {
            status[groupId] = 'error';
            socket.close();
        };
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const type = data.type || data.event;
                if (listeners[groupId] && listeners[groupId][type]) {
                    listeners[groupId][type].forEach(cb => cb(data));
                }
            } catch (err) {
                // 可选：日志
            }
        };
    }
    doConnect();
}

export function closeGroupSocket(groupId) {
    if (groupSockets[groupId]) {
        groupSockets[groupId].close();
        groupSockets[groupId] = null;
        status[groupId] = 'closed';
        if (reconnectTimers[groupId]) {
            clearTimeout(reconnectTimers[groupId]);
            reconnectTimers[groupId] = null;
        }
    }
}

export function sendGroupMessage(groupId, payload) {
    if (groupSockets[groupId] && groupSockets[groupId].readyState === WebSocket.OPEN) {
        groupSockets[groupId].send(JSON.stringify(payload));
    }
}

export function onGroupMessage(groupId, type, cb) {
    if (!listeners[groupId]) listeners[groupId] = {};
    if (!listeners[groupId][type]) listeners[groupId][type] = [];
    listeners[groupId][type].push(cb);
}

export function offGroupMessage(groupId, type, cb) {
    if (listeners[groupId] && listeners[groupId][type]) {
        listeners[groupId][type] = listeners[groupId][type].filter(fn => fn !== cb);
    }
}

export function getGroupSocketStatus(groupId) {
    return status[groupId] || 'closed';
} 