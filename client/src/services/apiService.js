import axios from 'axios';
const BASE_URL = import.meta.env.VITE_API_BASE;
axios.defaults.withCredentials = true;

/**
 * 记录异常反馈点击
 * @param {Object} payload
 * @param {string} payload.group_id
 * @param {string} payload.user_id
 * @param {string} payload.click_type  // 'More' | 'Less' | 'Share'
 * @param {string} payload.anomaly_analysis_results_id
 * @param {string} [payload.detail_type]
 * @param {string} [payload.detail_status]
 * @param {Array<string>} [payload.share_to_user_ids]
 */
function feedbackClick(payload) {
  return axios.post(`${BASE_URL}/analysis/anomaly_polling/feedback_click`, payload)
    .then(res => res.data);
}

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

  getLocalAnomalyStatus(data) {
    return axios.post(`${BASE_URL}/analysis/local_anomalies`, data).then(res => res.data);
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
  async getAnomalyResultsByUser(groupId, userId, page = 1, pageSize = 10) {
    const res = await fetch(`${BASE_URL}/analysis/anomaly_results_by_user?user_id=${userId}&page=${page}&page_size=${pageSize}`);
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

  feedbackClick,

  // 保存协作笔记内容
  saveNoteContent(data) {
    // data: { note_id, user_id, content, html, updated_at }
    return axios.post(`${BASE_URL}/api/note/content`, data).then(res => res.data);
  },

  // 保存协作笔记编辑历史
  saveNoteEditHistory(data) {
    // data: { note_id, user_id, delta, char_count, is_delete, has_header, has_list, updated_at, summary, affected_text }
    return axios.post(`${BASE_URL}/api/note/edit-history`, data).then(res => res.data);
  },

  // ===== group_data相关接口 =====
  getNoteEditHistoryByGroup(groupId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/note_edit_history/${groupId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getNoteContentsByGroup(groupId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/note_contents/${groupId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getPageBehaviorLogsByGroup(groupId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/pageBehaviorLogs/${groupId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getPageBehaviorLogsByUser(userId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/pageBehaviorLogs/user/${userId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getSpeechTranscriptsByGroup(groupId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/speech_transcripts/${groupId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getAnomalyAnalysisResultsByGroup(groupId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/anomaly_analysis_results/${groupId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  // 单条删除anomaly_analysis_results
  deleteAnomalyAnalysisResult(docId) {
    return axios.delete(`${BASE_URL}/api/group_data/anomaly_analysis_results/${docId}`).then(res => res.data);
  },
  // 批量删除anomaly_analysis_results
  batchDeleteAnomalyAnalysisResults(ids) {
    return axios.delete(`${BASE_URL}/api/group_data/anomaly_analysis_results/batch`, { data: { ids } }).then(res => res.data);
  },
  getNoteEditHistoryByUser(userId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/group_data/note_edit_history/user/${userId}`, {
      params: { page, page_size: pageSize }
    }).then(res => res.data);
  },
  getNoteContentsByUser(userId, page = 1, pageSize = 20) {
    return axios.get(`${BASE_URL}/api/notes/contents/user/${userId}?page=${page}&page_size=${pageSize}`).then(res => res.data);
  },

  // Peer Prompt 相关API
  sendPeerPrompt(data) {
    return axios.post(`${BASE_URL}/api/users/peer-prompt/send`, data).then(res => res.data);
  },

  getReceivedPeerPrompts(userId, groupId, page = 1, pageSize = 10) {
    return axios.get(`${BASE_URL}/api/users/peer-prompt/received?user_id=${userId}&group_id=${groupId}&page=${page}&page_size=${pageSize}`).then(res => res.data);
  },

  feedbackClick,
};