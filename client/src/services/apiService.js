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
  getAgendas(sessionId) {
    return axios.get(`${BASE_URL}/api/chat/agenda/session/${sessionId}`).then(res => res.data);
  },
  getChatSummaries(sessionId) {
    return axios.get(`${BASE_URL}/api/chat_summaries/session/${sessionId}`).then(res => res.data);
  },
  getUsers() {
    return axios.get(`${BASE_URL}/api/users/`).then(res => res.data);
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
  getUserAgent(userId) {
    return axios.get(`${BASE_URL}/api/users/${userId}/agent`).then(res => res.data);
  },
  getDiscussionInsightsByGroupAndAgent(groupId, agentId) {
    return axios
      .get(`${BASE_URL}/api/discussion_insights/${groupId}/agent/${agentId}`)
      .then(res => res.data);
  },
  updateAgenda(agendaId, data) {
    return axios.put(`${BASE_URL}/api/chat/agenda/${agendaId}`, data).then(res => res.data);
  },
  queryDiscussionInsights(payload) {
    return axios
      .post(`${BASE_URL}/api/discussion_insights`, payload)
      .then(res => res.data);
  },
  fetchLatestSummary(groupId) {
    return this.getChatSummariesByGroup(groupId);
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
  generatePrompt(groupId) {
    return axios.post(`${BASE_URL}/api/ai_bots/generate_prompt/${groupId}`).then(res => res.data);
  },
  getPromptVersions(botId, promptType, version = null) {
    const url = `${BASE_URL}/api/ai_prompt_versions/${botId}/${promptType}`;
    const params = version ? { version } : {};
    return axios.get(url, { params }).then(res => res.data);
  },
  updateUser(userId, data) {
    return axios.put(`${BASE_URL}/api/users/${userId}`, data).then(res => res.data);
  },
  generatePersonalPrompt(agentId) {
    return axios.post(`${BASE_URL}/api/personal_agents/generate_prompt/${agentId}`);
  },
  getPersonalPromptVersions(agentId) {
    const url = `${BASE_URL}/api/personal_prompt_versions/${agentId}`;
    return axios.get(url).then(res => res.data);
  },
  getBotModel(botId) {
    return axios.get(`${BASE_URL}/api/ai_bots/${botId}/model`).then(res => res.data);
  },
  updateBotModel(botId, model) {
    return axios.put(`${BASE_URL}/api/ai_bots/${botId}/model`, { model }).then(res => res.data);
  },
  getAgentModel(agentId) {
    return axios.get(`${BASE_URL}/api/personal_agents/${agentId}`).then(res => res.data);
  },
  updateAgentModel(agentId, model) {
    return axios.put(`${BASE_URL}/api/personal_agents/${agentId}/model`, { model }).then(res => res.data);
  },
  submitBotFeedback(payload) {
    return axios.post(`${BASE_URL}/api/ai_bots/feedback`, payload).then(res => res.data);
  },
  getBotFeedback(query) {
    return axios.get(`${BASE_URL}/api/ai_bots/feedback`, { params: query }).then(res => res.data);
  },
  submitAgentFeedback(payload) {
    return axios.post(`${BASE_URL}/api/ai_agents/feedback`, payload).then(res => res.data);
  },
  getAgentFeedback(query) {
    return axios.get(`${BASE_URL}/api/ai_agents/feedback`, { params: query }).then(res => res.data);
  },
  generateSummary(groupId, payload) {
    return axios.post(`${BASE_URL}/api/summary/generate_summary/${groupId}`, payload, {
      headers: {
        "Content-Type": "application/json"
      }
    }).then(res => res.data);
  },
  generateGuidance(groupId, payload) {
    return axios.post(`${BASE_URL}/api/summary/generate_guidance/${groupId}`, payload, {
      headers: {
        "Content-Type": "application/json"
      }
    }).then(res => res.data);
  },

};