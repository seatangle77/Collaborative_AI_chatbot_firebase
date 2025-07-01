import axios from 'axios';
const BASE_URL = import.meta.env.VITE_API_BASE;
axios.defaults.withCredentials = true;
export default {
  getAgenda() { return axios.get(`${BASE_URL}/api/chat/agenda`).then(res => res.data); },
  getTerm(word) { return axios.get(`${BASE_URL}/api/discussion/terms/${word}`).then(res => res.data); },
  getReview() { return axios.get(`${BASE_URL}/api/chat/review`).then(res => res.data); },
  getGroups() {
    return axios.get(`${BASE_URL}/api/groups`).then(res => res.data);
  },
  getGroupMembers(groupId) {
    return axios.get(`${BASE_URL}/api/groups/${groupId}/members`).then(res => res.data);
  },
  getSession(groupId) {
    return axios.get(`${BASE_URL}/api/sessions/${groupId}`).then(res => res.data);
  },
  getChatHistory(groupId) {
    return axios.get(`${BASE_URL}/api/chat/${groupId}`).then(res => res.data);
  },
  getChatSummaries(sessionId) {
    return axios.get(`${BASE_URL}/api/chat_summaries/session/${sessionId}`).then(res => res.data);
  },
  getUsers() {
    return axios.get(`${BASE_URL}/api/users/`).then(res => res.data);
  },
  getUserGroupContext(userId) {
    return axios.get(`${BASE_URL}/api/user/${userId}/group-context`).then(res => res.data);
  },
  getAiBots() {
    return axios.get(`${BASE_URL}/api/ai_bots`).then(res => res.data);
  },
  sendChatMessage(payload) {
    return axios.post(`${BASE_URL}/api/chat/send`, payload).then(res => res.data);
  },
  updateAgendaStatus(agendaId, status) {
    return axios.put(`${BASE_URL}/api/chat/agenda/${agendaId}`, { status }).then(res => res.data);
  },
  getChatSummariesByGroup(groupId) {
    return axios.get(`${BASE_URL}/api/chat_summaries/${groupId}`).then(res => res.data);
  },
  updateAgenda(agendaId, data) {
    return axios.put(`${BASE_URL}/api/chat/agenda/${agendaId}`, data).then(res => res.data);
  },
  toggleAgendaStatus(agendaId, status) {
    return axios.put(`${BASE_URL}/api/chat/agenda/${agendaId}`, { status }).then(res => res.data);
  },
  createAgenda(data) {
    return axios.post(`${BASE_URL}/api/chat/agenda`, data).then(res => res.data);
  },
  deleteAgenda(agendaId) {
    return axios.delete(`${BASE_URL}/api/chat/agenda/${agendaId}`).then(res => res.data);
  },
  updateGroupInfo(groupId, data) {
    return axios.put(`${BASE_URL}/api/groups/${groupId}`, data).then(res => res.data);
  },
  updateUser(userId, data) {
    return axios.put(`${BASE_URL}/api/users/${userId}`, data).then(res => res.data);
  },
  getBotModel(botId) {
    return axios.get(`${BASE_URL}/api/ai_bots/${botId}/model`).then(res => res.data);
  },
  updateBotModel(botId, model) {
    return axios.put(`${BASE_URL}/api/ai_bots/${botId}/model`, { model }).then(res => res.data);
  },
  resetAgendaStatus(groupId, stage) {
    return axios.patch(`${BASE_URL}/api/chat/agenda/reset_status/${groupId}?stage=${stage}`)
      .then(res => res.data);
  },

  getAnomalyStatus(data) {
    return axios.post(`${BASE_URL}/analysis/anomalies`, data).then(res => res.data);
  },

  getIntervalSummary(groupId, roundIndex, startTime, endTime, memberList) {
    return axios.post(`${BASE_URL}/analysis/interval_summary`, {
      group_id: groupId,
      round_index: roundIndex,
      start_time: startTime,
      end_time: endTime,
      members: memberList
    }).then(res => res.data);
  },

  getRoundSummaryCombined(groupId, roundIndex, startTime, endTime) {
    return axios.get(`${BASE_URL}/analysis/round_summary_combined`, {
      params: { group_id: groupId, round_index: roundIndex, start_time: startTime, end_time: endTime }
    }).then(res => res.data);
  },

  getAgendas(sessionId) {
    return axios.get(`${BASE_URL}/api/chat/agenda/session/${sessionId}`).then(res => res.data);
  },

  // 获取某用户历史异常分析结果
  async getAnomalyResultsByUser(groupId, userId) {
    const res = await fetch(`${BASE_URL}/analysis/anomaly_results_by_user?group_id=${groupId}&user_id=${userId}`);
    if (!res.ok) throw new Error('获取历史异常分析失败');
    return await res.json();
  },

  // 启动AI异常分析轮询
  async startAnomalyPolling(group_id) {
    return await axios.post(`${BASE_URL}/analysis/anomaly_polling/start`, { group_id });
  },

  // 停止AI异常分析轮询
  async stopAnomalyPolling(group_id) {
    return await axios.post(`${BASE_URL}/analysis/anomaly_polling/stop`, { group_id });
  },
};