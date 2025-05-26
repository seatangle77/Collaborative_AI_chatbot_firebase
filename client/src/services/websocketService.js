const sockets = {}; // 存储多个 WebSocket 连接

export const createWebSocket = (groupId) => {
  if (sockets[groupId]) {
    console.log(`⚡ WebSocket for Group ${groupId} already exists.`);
    return;
  }

  const WS_BASE_URL = import.meta.env.VITE_WS_BASE;
  const socket = new WebSocket(`${WS_BASE_URL}/ws/${groupId}`);
  sockets[groupId] = socket;

  socket.onopen = () => {
    console.log(`✅ WebSocket 连接成功: Group ${groupId}`);
  };

  socket.onmessage = (event) => {
    let receivedData = event.data;

    console.log("📩 WebSocket 收到原始数据:", receivedData);

    try {
      // 解析 JSON 数据
      if (typeof receivedData === "string") {
        receivedData = JSON.parse(receivedData);
      }

      console.log("✅ 解析后数据:", receivedData);

      // **区分不同类型的 WebSocket 消息**
      switch (receivedData.type) {
        case "message":
          console.log("💬 新聊天消息:", receivedData.message, "🆔 msgId:", receivedData.message?.msgId);
          break;

        case "ai_summary":
          console.log("🤖 AI 会议总结:", receivedData.summary_text);
          break;

        case "ai_guidance":
          console.log("🤖 AI 认知引导:", receivedData.message);
          if (onMessageCallback) {
            onMessageCallback(receivedData);
          }
          break;
        
        default:
          console.warn("⚠️ 未知类型的 WebSocket 消息:", receivedData);
      }

      // **通知 Vue 组件更新 UI**
      if (onMessageCallback) {
        onMessageCallback(receivedData);
      }
    } catch (error) {
      console.error("❌ WebSocket 消息解析失败:", error, "原始数据:", event.data);
    }
  };

  socket.onclose = () => {
    console.log(`⚠️ WebSocket 连接关闭: Group ${groupId}`);
    delete sockets[groupId];
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket 发生错误:", error);
  };
};

export const changeAiProviderAndTriggerSummary = (groupId, aiProvider) => {
  if (!groupId || !aiProvider) {
    console.error("⚠️ groupId 或 aiProvider 为空，无法触发 AI 会议总结");
    return;
  }

  // const payload = {
  //   type: "trigger_ai_summary",
  //   aiProvider, // ✅ 传递用户选择的 AI 供应商
  // };

  sendControlMessage(groupId, payload);
};

// 新增发送控制类系统消息方法
export const sendControlMessage = (groupId, payload) => {
  if (!groupId || !payload) {
    console.error("⚠️ groupId 或 payload 为空，无法发送控制消息");
    return;
  }

  if (sockets[groupId] && sockets[groupId].readyState === WebSocket.OPEN) {
    const data = JSON.stringify(payload);
    sockets[groupId].send(data);
    console.log("📤 发送控制消息:", data);
  } else {
    console.warn("⚠️ WebSocket 连接未打开，尝试创建连接后延迟发送控制消息");
    createWebSocket(groupId);
    // 延迟发送，等待连接打开
    const waitAndSend = () => {
      if (sockets[groupId] && sockets[groupId].readyState === WebSocket.OPEN) {
        const data = JSON.stringify(payload);
        sockets[groupId].send(data);
        console.log("📤 发送控制消息（延迟）:", data);
      } else {
        setTimeout(waitAndSend, 100);
      }
    };
    waitAndSend();
  }
};

// 恢复原来的 sendMessage 函数逻辑，发送用户正常聊天消息
export const sendMessage = (groupId, message) => {
  if (!message.msgId) {
    message.msgId = crypto.randomUUID?.() || Math.random().toString(36).substr(2, 9);
  }

  if (!message.created_at) {
    message.created_at = new Date().toISOString();
  }

  if (message.personal_agent_id === undefined) {
    message.personal_agent_id = ""; // 确保结构一致，即使为空
  }

  if (!message.chatbot_id) {
    message.chatbot_id = "default-bot-id"; // 可选：设置默认 bot_id 或从外部传入
  }

  if (sockets[groupId] && sockets[groupId].readyState === WebSocket.OPEN) {
    const payload = JSON.stringify(message);
    sockets[groupId].send(payload);
    console.log("📤 发送消息:", payload);
  } else {
    console.error("⚠️ WebSocket 连接未打开，无法发送消息");
  }
};

let onMessageCallback = null;

// ✅ **WebSocket 监听消息回调**
export const onMessageReceived = (callback) => {
  onMessageCallback = callback;
};

// ✅ **关闭 WebSocket**
export const closeWebSocket = (groupId) => {
  if (sockets[groupId]) {
    sockets[groupId].close();
    delete sockets[groupId];
  }
};