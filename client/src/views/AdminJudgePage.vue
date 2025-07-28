<template>
  <div class="admin-judge-root">
    <div class="controls-container">
      <div class="group-selector">
        <label for="group-select">选择小组：</label>
        <select id="group-select" v-model="selectedGroupId" @change="onGroupChange">
          <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
        </select>
      </div>
      
      <div class="time-selector">
        <div class="time-input-group">
          <label for="start-time">开始时间：</label>
          <input 
            id="start-time" 
            type="datetime-local" 
            v-model="startTime" 
            class="time-input"
          />
        </div>
        <div class="time-input-group">
          <label for="end-time">结束时间：</label>
          <input 
            id="end-time" 
            type="datetime-local" 
            v-model="endTime" 
            class="time-input"
          />
        </div>
        <button class="analyze-btn" @click="startAnalysis" :disabled="isAnalyzing">
          {{ isAnalyzing ? '分析中...' : '本地分析' }}
        </button>

        <div class="current-time-display">
          <span class="time-label">当前时间：</span>
          <input 
            type="datetime-local" 
            v-model="currentTimeLocal" 
            @change="updateCurrentTime"
            class="time-picker"
          />
          <span class="time-utc">UTC: {{ currentTime }}</span>
        </div>
        <button class="polling-btn" @click="startPollingAnalysis" :disabled="isPolling">
          {{ isPolling ? '轮询中...' : '轮询分析' }}
        </button>
        <button class="stop-polling-btn" @click="stopPollingAnalysis" :disabled="!isPolling">
          {{ isPolling ? '停止轮询' : '轮询已停止' }}
        </button>
      </div>
    </div>
    
    <div class="group-title">{{ currentGroupName }}</div>
    <div class="user-cards">
      <div class="user-card" v-for="user in users" :key="user.id">
        <div class="user-name">{{ user.name }}</div>
        
        <!-- 分析结果展示 -->
        <div v-if="user.analysis" class="analysis-results">
          <!-- 历史轮次标签 -->
          <div class="round-tabs">
            <div 
              v-for="(history, index) in user.analysisHistory" 
              :key="index"
              class="round-tab"
              :class="{ active: user.selectedRoundIndex === index }"
              @click="selectRound(user.id, index)"
            >
              第{{ history.round }}轮 <span v-if="history.start_time">{{ formatHourMinute(history.start_time) }}</span>
            </div>
          </div>

          <!-- 当前轮次数据 -->
          <div class="current-round-data">
            <!-- 发言数据 -->
            <div class="analysis-section">
              <div class="section-title">发言情况</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>发言比例</span>
                  <span class="progress-value">{{ getCurrentAnalysis(user).speech_percent }}</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill speech-fill" 
                    :style="{ width: parseFloat(getCurrentAnalysis(user).speech_percent) + '%' }"
                  ></div>
                </div>
                <div class="compact-data-grid">
                  <div class="data-item">
                    <span class="data-label">时长</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).speech_duration }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">等级</span>
                    <span class="level-badge" :class="getSpeechLevelClass(getCurrentAnalysis(user).speech_level)">
                      {{ getCurrentAnalysis(user).speech_level }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 笔记编辑数据 -->
            <div class="analysis-section">
              <div class="section-title">笔记编辑</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>编辑活跃度</span>
                  <span class="progress-value">{{ getCurrentAnalysis(user).note_edit_score * 100 }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill note-fill" 
                    :style="{ width: getCurrentAnalysis(user).note_edit_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="compact-data-grid">
                  <div class="data-item">
                    <span class="data-label">次数</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).note_edit_count }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">字符</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).note_edit_char_count }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">等级</span>
                    <span class="level-badge" :class="getNoteLevelClass(getCurrentAnalysis(user).note_edit_level)">
                      {{ getCurrentAnalysis(user).note_edit_level }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 浏览行为数据 -->
            <div class="analysis-section">
              <div class="section-title">浏览行为</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>浏览活跃度</span>
                  <span class="progress-value">{{ getCurrentAnalysis(user).browser_score * 100 }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill browser-fill" 
                    :style="{ width: getCurrentAnalysis(user).browser_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="compact-data-grid">
                  <div class="data-item">
                    <span class="data-label">页面</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).page_count }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">操作</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).mouse_action_count }}次</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">时长</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).mouse_duration }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">比例</span>
                    <span class="data-value">{{ getCurrentAnalysis(user).mouse_percent }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">等级</span>
                    <span class="level-badge" :class="getBrowserLevelClass(getCurrentAnalysis(user).browser_level)">
                      {{ getCurrentAnalysis(user).browser_level }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 总体评估 -->
            <div class="analysis-section total-section">
              <div class="section-title">总体评估</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>总参与度</span>
                  <span class="progress-value">{{ (getCurrentAnalysis(user).total_score * 100).toFixed(1) }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill total-fill" 
                    :style="{ width: getCurrentAnalysis(user).total_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="compact-data-grid">
                  <div class="data-item">
                    <span class="data-label">等级</span>
                    <span class="level-badge total-level" :class="getLevelClass(getCurrentAnalysis(user).total_level)">
                      {{ getCurrentAnalysis(user).total_level }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 历史对比 -->
          <div v-if="user.analysisHistory.length > 1" class="history-comparison">
            <div class="section-title">历史对比</div>
            <div class="history-chart">
              <div class="history-item" v-for="(history, index) in user.analysisHistory.slice(0, 3)" :key="index">
                <div class="history-round">第{{ history.round }}轮</div>
                <div class="history-scores">
                  <div class="score-item">
                    <span class="score-label">发言</span>
                    <div class="mini-progress">
                      <div class="mini-fill speech-fill" :style="{ width: parseFloat(history.speech_percent) + '%' }"></div>
                    </div>
                  </div>
                  <div class="score-item">
                    <span class="score-label">编辑</span>
                    <div class="mini-progress">
                      <div class="mini-fill note-fill" :style="{ width: history.note_edit_score * 100 + '%' }"></div>
                    </div>
                  </div>
                  <div class="score-item">
                    <span class="score-label">浏览</span>
                    <div class="mini-progress">
                      <div class="mini-fill browser-fill" :style="{ width: history.browser_score * 100 + '%' }"></div>
                    </div>
                  </div>
                  <div class="score-item">
                    <span class="score-label">总分</span>
                    <div class="mini-progress">
                      <div class="mini-fill total-fill" :style="{ width: history.total_score * 100 + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 无分析结果时的占位 -->
        <div v-else class="no-analysis">
          <div class="user-info">发言比例</div>
          <div class="user-info">行为数据比例</div>
          <div class="ai-tip">AI提示</div>
        </div>
        
                          <!-- AI提示数据区域 -->
        <div v-if="user.analysis" class="ai-suggestions-section">
          <!-- AI提示历史 -->
          <div class="analysis-section ai-history-section">
            <div class="section-title">AI提示历史</div>
            <div class="ai-history-list">
              <div 
                v-for="(suggestion, index) in user.aiHistory.slice(0, 3)" 
                :key="index"
                class="ai-history-item"
                @click="showAiDetail(user.id, suggestion)"
              >
                <div class="ai-summary">{{ suggestion.glasses_summary }}</div>
                <div class="ai-time">{{ formatTimeRange(suggestion.start_time, suggestion.end_time) }}</div>
              </div>
              <div v-if="user.aiHistory.length === 0" class="no-ai-history">
                暂无AI提示历史
              </div>
            </div>
          </div>
          
          <!-- 当前AI提示 -->
          <div class="analysis-section ai-current-section">
            <div class="section-title">即将发送的AI提示</div>
            <div v-if="user.currentAiSuggestion" class="ai-current-item">
              <div class="ai-summary" @click="showAiDetail(user.id, user.currentAiSuggestion)">
                {{ user.currentAiSuggestion.glasses_summary }}
              </div>
              <div class="ai-time">{{ formatTimeRange(user.currentAiSuggestion.start_time, user.currentAiSuggestion.end_time) }}</div>
              <div v-if="user.isCountdownActive && !user.isPushed" class="countdown-section">
                <div class="countdown-display">
                  <span class="countdown-label">倒计时:</span>
                  <span class="countdown-time" :class="{ 'urgent': user.countdownSeconds <= 10 }">
                    {{ formatCountdown(user.countdownSeconds) }}
                  </span>
                </div>
                <div class="countdown-actions">
                  <button 
                    @click="showImmediatePushModal(user.id)"
                    class="immediate-push-btn">
                    立即推送
                  </button>
                  <button 
                    @click="cancelNotification(user.id)"
                    class="cancel-send-btn">
                    取消发送
                  </button>
                </div>
              </div>
              <div v-else-if="user.isPushed" class="countdown-section">
                <div class="pushed-status">
                  <span class="pushed-label">✅ 已推送</span>
                </div>
              </div>
            </div>
            <div v-else class="no-ai-current">
              暂无即将发送的AI提示
            </div>
          </div>
        </div>
        
        <!-- 推送状态显示 -->
        <div v-if="user.currentAiSuggestion && user.isPushed" class="push-status">
          <span class="status-text">✅ 已推送</span>
        </div>
        <div v-else-if="!user.currentAiSuggestion" class="no-push-status">
          暂无推送状态
        </div>
      </div>
    </div>
    
    <!-- AI详情弹窗 -->
    <div v-if="showAiDetailModal" class="ai-detail-modal" @click="closeAiDetail">
      <div class="ai-detail-content" @click.stop>
        <div class="ai-detail-header">
          <h3>AI分析详情</h3>
          <button class="close-btn" @click="closeAiDetail">&times;</button>
        </div>
        <div class="ai-detail-body">
          <div v-if="selectedAiDetail" class="ai-detail-info">
            <div class="detail-section">
              <h4>眼镜提示</h4>
              <p class="glasses-summary">{{ selectedAiDetail.glasses_summary }}</p>
            </div>
            
            <div class="detail-section">
              <h4>时间范围</h4>
              <p>{{ formatTimeRange(selectedAiDetail.start_time, selectedAiDetail.end_time) }}</p>
            </div>
            
            <div class="detail-section">
              <h4>参与度分析</h4>
              <p><strong>类型：</strong>{{ selectedAiDetail.detail?.type || '未知' }}</p>
              <p><strong>状态：</strong>{{ selectedAiDetail.detail?.status || '未知' }}</p>
              <p><strong>建议：</strong>{{ selectedAiDetail.detail?.suggestion || '无' }}</p>
            </div>
            
            <div class="detail-section">
              <h4>详细证据</h4>
              <pre class="evidence-text">{{ selectedAiDetail.detail?.evidence || '无' }}</pre>
            </div>
            
            <div v-if="selectedAiDetail.more_info" class="detail-section">
              <h4>额外信息</h4>
              <p><strong>协作建议：</strong>{{ selectedAiDetail.more_info.collaboration_suggestion || '无' }}</p>
              <p><strong>详细原因：</strong>{{ selectedAiDetail.more_info.detailed_reason || '无' }}</p>
              <p><strong>历史对比：</strong>{{ selectedAiDetail.more_info.history_comparison || '无' }}</p>
              <p><strong>小组对比：</strong>{{ selectedAiDetail.more_info.group_comparison || '无' }}</p>
            </div>
            
            <div v-if="selectedAiDetail.group_distribution" class="detail-section">
              <h4>小组分布</h4>
              <p><strong>小组类型：</strong>{{ selectedAiDetail.group_distribution.group_type || '未知' }}</p>
              <p><strong>小组风险：</strong>{{ selectedAiDetail.group_distribution.group_risk || '无' }}</p>
              <p><strong>行动提示：</strong>{{ selectedAiDetail.group_distribution.action_hint || '无' }}</p>
              <div class="distribution-stats">
                <span class="stat-item">主导: {{ selectedAiDetail.group_distribution.dominant || 0 }}</span>
                <span class="stat-item">高参与: {{ selectedAiDetail.group_distribution.high || 0 }}</span>
                <span class="stat-item">正常: {{ selectedAiDetail.group_distribution.normal || 0 }}</span>
                <span class="stat-item">低参与: {{ selectedAiDetail.group_distribution.low || 0 }}</span>
                <span class="stat-item">无参与: {{ selectedAiDetail.group_distribution.no || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 立即推送编辑模态框 -->
    <div v-if="immediatePushModalVisible" class="modal-overlay" @click="cancelImmediatePush">
      <div class="immediate-push-modal" @click.stop>
        <div class="modal-header">
          <h3>编辑推送内容</h3>
          <button class="close-btn" @click="cancelImmediatePush">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Summary:</label>
            <textarea 
              v-model="editedSummary" 
              placeholder="请输入summary内容"
              rows="4"
              class="form-textarea">
            </textarea>
          </div>
          <div class="form-group">
            <label>Glasses Summary:</label>
            <textarea 
              v-model="editedGlassesSummary" 
              placeholder="请输入glasses_summary内容"
              rows="3"
              class="form-textarea">
            </textarea>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="confirmImmediatePush" class="confirm-btn">立即推送</button>
          <button @click="cancelImmediatePush" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiService from '@/services/apiService';

export default {
  name: 'AdminJudgePage',
  data() {
    return {
      groups: [],
      selectedGroupId: '',
      users: [], // 展示用，包含id和name
      allUsers: [], // 所有用户信息
      startTime: '',
      endTime: '',
      isAnalyzing: false,
      isPolling: false,
      pollingInterval: null, // 存储定时器ID
      analysisHistory: {}, // 存储每个用户的历史分析数据 {userId: [{round1}, {round2}, {round3}]}
      currentRound: 1, // 当前轮次
              showAiDetailModal: false, // AI详情弹窗显示状态
        selectedAiDetail: null, // 选中的AI详情数据
        currentTime: '2025-07-28T04:10:00', // UTC时间，用于调试
        currentTimeLocal: '', // 本地时间选择器值
        lastTimeRange: null, // 记录上一次的时间范围，用于判断是否需要更新
        immediatePushModalVisible: false, // 立即推送模态框显示状态
        editingUserId: null, // 正在编辑的用户ID
        editedSummary: '', // 编辑后的summary
        editedGlassesSummary: '', // 编辑后的glasses_summary
      lastAiTimeRange: null, // 记录上一次AI分析的时间范围，用于判断是否需要更新
      lastNextNotifyTimeRange: null, // 记录上一次即将推送的时间范围，用于判断是否需要更新
      lastNextNotifyTime: null, // 记录上一次的next_notify_time，用于判断推送是否完成
      countdownTimers: {}, // 存储每个用户的倒计时定时器 {userId: timerId}
      countdownSeconds: {}, // 存储每个用户的倒计时秒数 {userId: seconds}
      cancelledNotifications: new Set(), // 存储已取消的推送通知
      timeUpdateInterval: null, // 时间更新定时器ID
    };
  },
  computed: {
    currentGroupName() {
      const group = this.groups.find(g => g.id === this.selectedGroupId);
      return group ? group.name : '';
    }
  },
  methods: {
    async fetchGroups() {
      const res = await apiService.getGroups();
      this.groups = res;
      if (res.length > 0) {
        this.selectedGroupId = res[0].id;
        this.fetchGroupMembers(res[0].id);
      }
    },
    async fetchAllUsers() {
      const res = await apiService.getUsers();
      this.allUsers = res;
    },
    async fetchGroupMembers(groupId) {
      const members = await apiService.getGroupMembers(groupId);
      this.users = members.map(member => {
        const userId = member.user_id || member.id;
        const userInfo = this.allUsers.find(u => String(u.user_id || u.id) === String(userId));
        return {
          id: userId,
          name: userInfo ? userInfo.name : (member.name || '未知用户'),
          device_token: userInfo ? userInfo.device_token : null, // 添加device_token
          pushLoading: false, // 初始化推送状态
        };
      });
    },
    async onGroupChange() {
      await this.fetchGroupMembers(this.selectedGroupId);
    },
    updateUserCardsWithAnalysis(analysisResult, roundStartTime, roundNumber = null) {
      // 更新用户卡片显示分析结果，并保存历史数据
      this.users = this.users.map(user => {
        // 根据用户ID匹配分析结果
        const userAnalysis = analysisResult[user.id];
        if (userAnalysis) {
          console.log(`更新用户 ${user.name} (${user.id}) 的分析数据`);
          
          // 保存到历史记录
          if (!this.analysisHistory[user.id]) {
            this.analysisHistory[user.id] = [];
          }
          
          // 使用传入的轮次号，如果没有则使用当前轮次
          const currentRound = roundNumber || this.currentRound;
          
          // 添加轮次信息
          const analysisWithRound = {
            ...userAnalysis,
            round: currentRound,
            timestamp: Date.now(),
            start_time: roundStartTime
          };
          
          // 检查是否已存在相同轮次的数据，如果存在则更新，否则添加
          const existingIndex = this.analysisHistory[user.id].findIndex(item => item.round === currentRound);
          if (existingIndex !== -1) {
            // 更新现有轮次数据
            this.analysisHistory[user.id][existingIndex] = analysisWithRound;
          } else {
            // 添加新轮次数据到开头（最新的在前面）
            this.analysisHistory[user.id].unshift(analysisWithRound);
          }
          
          // 按轮次排序（最新的在前面）
          this.analysisHistory[user.id].sort((a, b) => b.round - a.round);
          
          // 只保留最新3轮
          if (this.analysisHistory[user.id].length > 3) {
            this.analysisHistory[user.id] = this.analysisHistory[user.id].slice(0, 3);
          }
          
          return {
            ...user,
            analysis: userAnalysis,
            analysisHistory: this.analysisHistory[user.id],
            selectedRoundIndex: 0, // 默认选中最新轮次
            aiHistory: user.aiHistory || [], // 保持现有AI提示历史
            currentAiSuggestion: user.currentAiSuggestion || null // 保持现有AI提示
          };
        } else {
          console.log(`用户 ${user.name} (${user.id}) 在此轮次中无分析数据`);
        }
        return user;
      });
      
      // 只有在没有传入轮次号时才递增当前轮次
      if (!roundNumber) {
        this.currentRound++;
      }
    },
    hasTimeRangeChanged(currentTimeRange) {
      // 比较当前时间范围与上次记录的时间范围是否发生变化
      if (!currentTimeRange) {
        return false;
      }
      
      if (!this.lastTimeRange) {
        // 第一次获取数据，需要更新
        return true;
      }
      
      // 比较开始时间和结束时间
      const startChanged = currentTimeRange.start !== this.lastTimeRange.start;
      const endChanged = currentTimeRange.end !== this.lastTimeRange.end;
      
      return startChanged || endChanged;
    },
    hasAiTimeRangeChanged(currentAiTimeRange) {
      // 比较当前AI分析时间范围与上次记录的时间范围是否发生变化
      if (!currentAiTimeRange) {
        return false;
      }
      
      if (!this.lastAiTimeRange) {
        // 第一次获取数据，需要更新
        return true;
      }
      
      // 比较开始时间和结束时间
      const startChanged = currentAiTimeRange.start !== this.lastAiTimeRange.start;
      const endChanged = currentAiTimeRange.end !== this.lastAiTimeRange.end;
      
      return startChanged || endChanged;
    },
    hasNextNotifyTimeRangeChanged(currentNextNotifyTimeRange) {
      // 比较当前即将推送时间范围与上次记录的时间范围是否发生变化
      if (!currentNextNotifyTimeRange) {
        return false;
      }
      
      if (!this.lastNextNotifyTimeRange) {
        // 第一次获取数据，需要更新
        return true;
      }
      
      // 比较开始时间和结束时间
      const startChanged = currentNextNotifyTimeRange.start !== this.lastNextNotifyTimeRange.start;
      const endChanged = currentNextNotifyTimeRange.end !== this.lastNextNotifyTimeRange.end;
      
      return startChanged || endChanged;
    },
    // 检查是否需要更新即将推送数据
    shouldUpdateNextNotifyData(nextNotifyResult) {
      // 第一次获取数据，需要更新
      if (!this.lastNextNotifyTimeRange) {
        return true;
      }
      
      // 检查时间范围是否发生变化
      const timeRangeChanged = this.hasNextNotifyTimeRangeChanged(nextNotifyResult.time_range);
      if (timeRangeChanged) {
        return true;
      }
      
      // 检查last_notify_time是否与上次的next_notify_time相同
      const currentLastNotifyTime = this.extractLastNotifyTime(nextNotifyResult);
      if (currentLastNotifyTime && this.lastNextNotifyTime && currentLastNotifyTime === this.lastNextNotifyTime) {
        console.log('检测到推送完成，需要更新数据');
        console.log('当前last_notify_time:', currentLastNotifyTime);
        console.log('上次next_notify_time:', this.lastNextNotifyTime);
        return true;
      }
      
      return false;
    },
    // 提取next_notify_time
    extractNextNotifyTime(nextNotifyResult) {
      // 从所有用户数据中提取next_notify_time
      for (const userId in nextNotifyResult) {
        if (userId !== 'time_range' && nextNotifyResult[userId] && nextNotifyResult[userId].next_notify_time) {
          return nextNotifyResult[userId].next_notify_time;
        }
      }
      return null;
    },
    // 提取last_notify_time
    extractLastNotifyTime(nextNotifyResult) {
      // 从所有用户数据中提取last_notify_time
      for (const userId in nextNotifyResult) {
        if (userId !== 'time_range' && nextNotifyResult[userId] && nextNotifyResult[userId].last_notify_time) {
          return nextNotifyResult[userId].last_notify_time;
        }
      }
      return null;
    },
    formatHourMinute(timeStr) {
      // timeStr: '2025-07-10T07:02:00' - 需要明确解析为UTC时间
      if (!timeStr) return '';
      
      // 方法1: 如果时间字符串没有Z后缀，手动解析
      const match = timeStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
      if (match) {
        const [, year, month, day, hour, minute, second] = match;
        // 直接解析为UTC时间的小时和分钟
        const utcHour = parseInt(hour);
        const utcMinute = parseInt(minute);
        // 转换为东八区
        const beijingHour = (utcHour + 8) % 24;
        const h = String(beijingHour).padStart(2, '0');
        const m = String(utcMinute).padStart(2, '0');
        return `${h}:${m}`;
      }
      
      // 方法2: 备用方案，使用Date对象
      const d = new Date(timeStr);
      const utcHours = d.getUTCHours();
      const utcMinutes = d.getUTCMinutes();
      const beijingHours = (utcHours + 8) % 24;
      const h = String(beijingHours).padStart(2, '0');
      const m = String(utcMinutes).padStart(2, '0');
      
      return `${h}:${m}`;
    },
    selectRound(userId, roundIndex) {
      // 选择轮次
      this.users = this.users.map(user => {
        if (user.id === userId) {
          return {
            ...user,
            selectedRoundIndex: roundIndex
          };
        }
        return user;
      });
    },
    getCurrentAnalysis(user) {
      // 获取当前选中轮次的分析数据
      if (!user.analysisHistory || user.analysisHistory.length === 0) {
        return user.analysis || {};
      }
      
      const selectedIndex = user.selectedRoundIndex || 0;
      const selectedAnalysis = user.analysisHistory[selectedIndex];
      
      if (selectedAnalysis) {
        // 移除轮次相关的字段，只返回分析数据
        const { round, timestamp, start_time, ...analysisData } = selectedAnalysis;
        return analysisData;
      }
      
      return user.analysis || {};
    },
    formatTimeRange(startTime, endTime) {
      if (!startTime || !endTime) return '';
      
      const start = this.formatHourMinute(startTime);
      const end = this.formatHourMinute(endTime);
      
      return `${start} - ${end}`;
    },
    formatCountdown(seconds) {
      if (seconds <= 0) return '00:00';
      
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      
      const result = `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
      console.log(`格式化倒计时: ${seconds}秒 -> ${result}`);
      
      return result;
    },
    showAiDetail(userId, aiData) {
      if (!aiData) return;
      
      this.selectedAiDetail = aiData;
      this.showAiDetailModal = true;
    },
    closeAiDetail() {
      this.showAiDetailModal = false;
      this.selectedAiDetail = null;
    },

    updateCurrentTime() {
      // 将本地时间转换为UTC时间
      if (this.currentTimeLocal) {
        // 解析本地时间字符串
        const match = this.currentTimeLocal.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
        if (match) {
          const [, year, month, day, hour, minute] = match;
          
          // 将东八区时间转换为UTC时间（减8小时）
          let utcHour = parseInt(hour) - 8;
          let utcDay = parseInt(day);
          let utcMonth = parseInt(month);
          let utcYear = parseInt(year);
          
          // 处理跨日的情况
          if (utcHour < 0) {
            utcHour += 24;
            utcDay -= 1;
            
            // 处理跨月的情况
            if (utcDay < 1) {
              utcMonth -= 1;
              if (utcMonth < 1) {
                utcMonth = 12;
                utcYear -= 1;
              }
              const daysInMonth = new Date(utcYear, utcMonth, 0).getDate();
              utcDay = daysInMonth;
            }
          }
          
          // 格式化为UTC时间字符串
          this.currentTime = `${utcYear}-${String(utcMonth).padStart(2, '0')}-${String(utcDay).padStart(2, '0')}T${String(utcHour).padStart(2, '0')}:${minute}:00`;
          
          console.log('用户手动更新时间:', this.currentTime);
          
          // 如果正在轮询，重新启动时间更新定时器
          if (this.isPolling) {
            this.startTimeUpdate();
          }
        }
      }
    },
    // 将UTC时间转换为本地时间（东八区）
    convertUtcToLocal(utcTime) {
      if (!utcTime) return '';
      
      // 解析UTC时间字符串
      const match = utcTime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
      if (!match) {
        console.error('UTC时间格式错误:', utcTime);
        return '';
      }
      
      const [, year, month, day, hour, minute, second] = match;
      
      // 转换为东八区时间（加8小时）
      let beijingHour = parseInt(hour) + 8;
      let beijingDay = parseInt(day);
      let beijingMonth = parseInt(month);
      let beijingYear = parseInt(year);
      
      // 处理跨日的情况
      if (beijingHour >= 24) {
        beijingHour -= 24;
        beijingDay += 1;
        
        // 处理跨月的情况
        const daysInMonth = new Date(beijingYear, beijingMonth, 0).getDate();
        if (beijingDay > daysInMonth) {
          beijingDay = 1;
          beijingMonth += 1;
          
          // 处理跨年的情况
          if (beijingMonth > 12) {
            beijingMonth = 1;
            beijingYear += 1;
          }
        }
      }
      
      // 格式化为本地时间选择器格式 (YYYY-MM-DDTHH:MM)
      const result = `${beijingYear}-${String(beijingMonth).padStart(2, '0')}-${String(beijingDay).padStart(2, '0')}T${String(beijingHour).padStart(2, '0')}:${minute}`;
      
      console.log(`UTC时间转换: ${utcTime} -> 东八区时间: ${result}`);
      
      return result;
    },
    // 更新用户AI提示历史数据
    updateUserAiHistoryData(aiAnalysisResult, roundStartTime, roundNumber) {
      console.log(`更新第${roundNumber}轮AI分析数据:`, aiAnalysisResult);
      
      // 更新用户卡片显示AI分析结果
      this.users = this.users.map(user => {
        // 根据用户ID匹配AI分析结果
        const userAiData = aiAnalysisResult[user.id];
        if (userAiData) {
          console.log(`更新用户 ${user.name} (${user.id}) 的AI分析数据`);
          
          // 添加时间范围和轮次信息
          const aiDataWithTime = {
            ...userAiData,
            start_time: roundStartTime,
            end_time: roundStartTime ? this.addTwoMinutes(roundStartTime) : null,
            round: roundNumber
          };
          
          // 更新用户的AI提示历史
          const currentAiHistory = user.aiHistory || [];
          
          // 检查是否已存在相同轮次的AI数据，如果存在则更新，否则添加
          const existingIndex = currentAiHistory.findIndex(item => item.round === roundNumber);
          if (existingIndex !== -1) {
            // 更新现有轮次数据
            currentAiHistory[existingIndex] = aiDataWithTime;
          } else {
            // 添加新轮次数据到开头（最新的在前面）
            currentAiHistory.unshift(aiDataWithTime);
          }
          
          // 按轮次排序（最新的在前面）
          currentAiHistory.sort((a, b) => b.round - a.round);
          
          // 只保留最新3轮
          const updatedAiHistory = currentAiHistory.slice(0, 3);
          
          return {
            ...user,
            aiHistory: updatedAiHistory,
            currentAiSuggestion: user.currentAiSuggestion || null // 保持现有即将推送的AI提示
          };
        } else {
          console.log(`用户 ${user.name} (${user.id}) 在此轮次中无AI分析数据`);
        }
        return user;
      });
    },
    // 辅助方法：给时间加2分钟
    addTwoMinutes(timeStr) {
      if (!timeStr) return null;
      
      const date = new Date(timeStr);
      date.setMinutes(date.getMinutes() + 2);
      return date.toISOString().slice(0, 19);
    },
    // 计算倒计时秒数
    calculateCountdown(nextNotifyTime) {
      if (!nextNotifyTime) return 0;
      
      console.log('=== 倒计时计算开始 ===');
      console.log('原始nextNotifyTime:', nextNotifyTime);
      console.log('页面currentTime:', this.currentTime);
      
      // 解析UTC时间字符串，移除+00:00后缀
      const cleanTime = nextNotifyTime.replace('+00:00', '');
      console.log('清理后的时间:', cleanTime);
      
      const now = new Date(this.currentTime); // 使用页面当前时间
      const notifyTime = new Date(cleanTime);
      
      console.log('创建的时间对象:', {
        now: now.toISOString(),
        notifyTime: notifyTime.toISOString(),
        nowTimestamp: now.getTime(),
        notifyTimestamp: notifyTime.getTime()
      });
      
      const diffSeconds = Math.floor((notifyTime - now) / 1000);
      console.log('时间差秒数:', diffSeconds);
      console.log('时间差小时:', Math.floor(diffSeconds / 3600));
      console.log('时间差天数:', Math.floor(diffSeconds / 86400));
      
      // 如果是负数，返回5秒倒计时
      if (diffSeconds < 0) {
        console.log('时间差为负数，返回5秒倒计时');
        return 5;
      }
      
      console.log('=== 倒计时计算结束 ===');
      return diffSeconds;
    },
    // 启动倒计时
    startCountdown(userId, initialSeconds, aiData) {
      // 清除现有的倒计时
      this.clearCountdown(userId);
      
      let seconds = initialSeconds;
      
      // 立即更新用户数据
      const userIndex = this.users.findIndex(u => u.id === userId);
      if (userIndex !== -1) {
        this.users[userIndex] = {
          ...this.users[userIndex],
          countdownSeconds: seconds,
          isCountdownActive: true
        };
      }
      
      const timer = setInterval(() => {
        seconds--;
        
        // 更新用户数据中的倒计时
        const userIndex = this.users.findIndex(u => u.id === userId);
        if (userIndex !== -1) {
          this.users[userIndex] = {
            ...this.users[userIndex],
            countdownSeconds: seconds
          };
        }
        
        console.log(`用户 ${userId} 倒计时: ${seconds}秒`);
        
        if (seconds <= 0) {
          // 倒计时结束，自动推送
          this.clearCountdown(userId);
          this.autoSendPush(userId, aiData);
        }
      }, 1000);
      
      this.countdownTimers[userId] = timer;
      console.log(`用户 ${userId} 倒计时启动，初始秒数: ${initialSeconds}`);
    },
    // 清除单个用户的倒计时
    clearCountdown(userId) {
      if (this.countdownTimers[userId]) {
        clearInterval(this.countdownTimers[userId]);
        delete this.countdownTimers[userId];
      }
      delete this.countdownSeconds[userId];
      
      // 更新用户数据
      const userIndex = this.users.findIndex(u => u.id === userId);
      if (userIndex !== -1) {
        this.users[userIndex] = {
          ...this.users[userIndex],
          countdownSeconds: 0,
          isCountdownActive: false
        };
      }
    },
    // 清除所有倒计时
    clearAllCountdowns() {
      Object.keys(this.countdownTimers).forEach(userId => {
        this.clearCountdown(userId);
      });
    },
    // 取消推送
    cancelNotification(userId) {
      const user = this.users.find(u => u.id === userId);
      if (user && user.currentAiSuggestion) {
        const notificationKey = `${userId}_${user.currentAiSuggestion.next_notify_time}`;
        this.cancelledNotifications.add(notificationKey);
        
        // 清除倒计时
        this.clearCountdown(userId);
        
        console.log(`用户 ${user.name} 的推送已取消`);
      }
    },
    // 启动时间更新
    startTimeUpdate() {
      // 清除现有的时间更新定时器
      this.stopTimeUpdate();
      
      // 每秒更新当前时间
      this.timeUpdateInterval = setInterval(() => {
        // 解析当前UTC时间
        const match = this.currentTime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
        if (match) {
          const [, year, month, day, hour, minute, second] = match;
          
          // 增加1秒
          let newSecond = parseInt(second) + 1;
          let newMinute = parseInt(minute);
          let newHour = parseInt(hour);
          let newDay = parseInt(day);
          let newMonth = parseInt(month);
          let newYear = parseInt(year);
          
          // 处理进位
          if (newSecond >= 60) {
            newSecond = 0;
            newMinute += 1;
            
            if (newMinute >= 60) {
              newMinute = 0;
              newHour += 1;
              
              if (newHour >= 24) {
                newHour = 0;
                newDay += 1;
                
                // 处理跨月
                const daysInMonth = new Date(newYear, newMonth, 0).getDate();
                if (newDay > daysInMonth) {
                  newDay = 1;
                  newMonth += 1;
                  
                  if (newMonth > 12) {
                    newMonth = 1;
                    newYear += 1;
                  }
                }
              }
            }
          }
          
          // 更新当前时间
          this.currentTime = `${newYear}-${String(newMonth).padStart(2, '0')}-${String(newDay).padStart(2, '0')}T${String(newHour).padStart(2, '0')}:${String(newMinute).padStart(2, '0')}:${String(newSecond).padStart(2, '0')}`;
          
          // 同时更新本地时间选择器
          this.currentTimeLocal = this.convertUtcToLocal(this.currentTime);
          
          console.log('当前时间更新:', this.currentTime);
        }
      }, 1000);
      
      console.log('时间更新定时器已启动');
    },
    
    // 停止时间更新
    stopTimeUpdate() {
      if (this.timeUpdateInterval) {
        clearInterval(this.timeUpdateInterval);
        this.timeUpdateInterval = null;
        console.log('时间更新定时器已停止');
      }
    },
    
    // 自动推送
    async autoSendPush(userId, aiData) {
      const user = this.users.find(u => u.id === userId);
      if (!user) return;
      
      console.log(`自动推送用户 ${user.name} 的AI提示`);
      
      try {
        // 从用户信息中获取device_token
        const deviceToken = user.device_token || user.deviceToken || "default_device_token";
        
        // 准备推送参数
        const pushPayload = {
          push_ji: true,
          device_token: deviceToken,
          glasses_summary: aiData.glasses_summary,
          summary: aiData.summary || `${user.name}的AI分析提示`,
          detail_suggestion: aiData.detail?.suggestion || "继续保持良好的参与状态",
          user_id: userId,
          user_name: user.name,
          push_pc: true,
          ai_analyze_result: aiData
        };

        console.log('自动推送参数:', pushPayload);
        console.log('用户device_token:', deviceToken);
        console.log('推送目标用户ID:', userId);
        
        // 调用推送接口
        const response = await apiService.pushAiAnalysisResult(pushPayload);
        console.log('自动推送成功:', response);
        
        // 更新用户状态
        const userIndex = this.users.findIndex(u => u.id === userId);
        if (userIndex !== -1) {
          this.users[userIndex] = {
            ...this.users[userIndex],
            isCountdownActive: false,
            countdownSeconds: 0,
            isPushed: true // 标记已推送
          };
        }
        
        console.log(`用户 ${user.name} 的自动推送完成`);
        
      } catch (error) {
        console.error('自动推送失败:', error);
      }
    },

    // 显示立即推送模态框
    showImmediatePushModal(userId) {
      const user = this.users.find(u => u.id === userId);
      if (!user || !user.currentAiSuggestion) return;
      
      this.editingUserId = userId;
      // 预填充原始内容
      this.editedSummary = user.currentAiSuggestion.summary || '';
      this.editedGlassesSummary = user.currentAiSuggestion.glasses_summary || '';
      this.immediatePushModalVisible = true;
    },

    // 确认立即推送
    async confirmImmediatePush() {
      if (!this.editingUserId) return;
      
      const user = this.users.find(u => u.id === this.editingUserId);
      if (!user || !user.currentAiSuggestion) return;
      
      // 创建修改后的AI数据
      const modifiedAiData = {
        ...user.currentAiSuggestion,
        summary: this.editedSummary,
        glasses_summary: this.editedGlassesSummary
      };
      
      // 调用推送
      await this.autoSendPush(this.editingUserId, modifiedAiData);
      
      // 关闭模态框
      this.immediatePushModalVisible = false;
      this.editingUserId = null;
      this.editedSummary = '';
      this.editedGlassesSummary = '';
    },

    // 取消立即推送
    cancelImmediatePush() {
      this.immediatePushModalVisible = false;
      this.editingUserId = null;
      this.editedSummary = '';
      this.editedGlassesSummary = '';
    },
    
    // 更新即将推送的AI提示数据
    updateNextNotifyData(nextNotifyResult) {
      console.log('更新即将推送的AI提示数据:', nextNotifyResult);
      
      // 根据用户ID匹配即将推送的AI提示数据
      this.users = this.users.map(user => {
        const userNotifyData = nextNotifyResult[user.id];
        if (userNotifyData) {
          console.log(`更新用户 ${user.name} (${user.id}) 的即将推送AI提示数据`);
          
          // 检查是否已取消该推送
          const notificationKey = `${user.id}_${userNotifyData.next_notify_time}`;
          if (this.cancelledNotifications.has(notificationKey)) {
            console.log(`用户 ${user.name} 的推送已被取消，跳过倒计时`);
            return {
              ...user,
              currentAiSuggestion: userNotifyData,
              countdownSeconds: 0,
              isCountdownActive: false
            };
          }
          
          // 计算倒计时秒数
          const countdownSeconds = this.calculateCountdown(userNotifyData.next_notify_time);
          
          // 启动倒计时
          this.startCountdown(user.id, countdownSeconds, userNotifyData);
          
          return {
            ...user,
            currentAiSuggestion: userNotifyData,
            countdownSeconds: countdownSeconds,
            isCountdownActive: true
          };
        } else {
          console.log(`用户 ${user.name} (${user.id}) 无即将推送的AI提示数据`);
        }
        return user;
      });
    },
    
    getLevelClass(level) {
      // 根据参与等级返回对应的CSS类名
      const levelMap = {
        'No Participation': 'level-no',
        'Low Participation': 'level-low',
        'Normal Participation': 'level-normal',
        'High Participation': 'level-high',
        'Dominant': 'level-dominant'
      };
      return levelMap[level] || 'level-normal';
    },
    getSpeechLevelClass(level) {
      // 根据发言等级返回对应的CSS类名
      const levelMap = {
        'No Speech': 'level-no',
        'Low Speech': 'level-low',
        'Normal Speech': 'level-normal',
        'High Speech': 'level-high',
        'Dominant Speech': 'level-dominant'
      };
      return levelMap[level] || 'level-normal';
    },
    getNoteLevelClass(level) {
      // 根据笔记编辑等级返回对应的CSS类名
      const levelMap = {
        'No Edit': 'level-no',
        'Low Edit': 'level-low',
        'Normal Edit': 'level-normal',
        'High Edit': 'level-high',
        'Frequent Edit': 'level-dominant'
      };
      return levelMap[level] || 'level-normal';
    },
    getBrowserLevelClass(level) {
      // 根据浏览等级返回对应的CSS类名
      const levelMap = {
        'No Browsing': 'level-no',
        'Few Browsing': 'level-low',
        'Normal Browsing': 'level-normal',
        'Frequent Browsing': 'level-high',
        'Excessive Browsing': 'level-dominant'
      };
      return levelMap[level] || 'level-normal';
    },
    async startAnalysis() {
      if (this.isAnalyzing) return;
      
      // 验证时间输入
      if (!this.startTime || !this.endTime) {
        alert('请选择开始时间和结束时间');
        return;
      }
      
      if (new Date(this.startTime) >= new Date(this.endTime)) {
        alert('开始时间必须早于结束时间');
        return;
      }
      
      this.isAnalyzing = true;
      try {
        // 转换时间格式为ISO字符串（本地时间转UTC）
        const startTimeDate = new Date(this.startTime);
        const endTimeDate = new Date(this.endTime);
        
        const startTimeISO = startTimeDate.toISOString().slice(0, 19);
        const endTimeISO = endTimeDate.toISOString().slice(0, 19);
        
        // 准备请求数据（简化后的版本，不再需要 current_user）
        const analysisData = {
          group_id: this.selectedGroupId,
          round_index: 1,
          start_time: startTimeISO,
          end_time: endTimeISO,
          members: this.users.map(user => ({
            id: user.id,
            name: user.name
          }))
        };
        
        console.log('开始本地分析...', analysisData);
        const result = await apiService.getLocalAnomalyStatus(analysisData);
        
        if (result.local_analysis) {
          console.log('分析结果:', result.local_analysis);
          console.log(`分析完成！处理时间: ${result.processing_time.toFixed(2)}秒`);
          
          // 更新用户卡片显示分析结果（本地分析使用特殊轮次号999）
          const roundStartTime = result.raw_data_summary?.time_range?.start;
          this.updateUserCardsWithAnalysis(result.local_analysis, roundStartTime, 999);
        } else {
          console.log('分析完成，但无数据结果');
        }
      } catch (error) {
        console.error('分析失败:', error);
        alert('分析失败：' + (error.message || '未知错误'));
      } finally {
        this.isAnalyzing = false;
      }
    },
    async startPollingAnalysis() {
      if (this.isPolling) return;
      
      // 验证时间输入
      if (!this.startTime || !this.endTime) {
        alert('请选择开始时间和结束时间');
        return;
      }
      
      this.isPolling = true;
      // 重置时间范围记录，确保第一次轮询会更新数据
      this.lastTimeRange = null;
      this.lastAiTimeRange = null;
      this.lastNextNotifyTimeRange = null;
      this.lastNextNotifyTime = null;
      // 清除所有倒计时和取消记录
      this.clearAllCountdowns();
      this.cancelledNotifications.clear();
      
      // 启动时间更新定时器，每秒更新当前时间
      this.startTimeUpdate();
      
      // 立即执行一次分析
      await this.performPollingAnalysis();
      // 设置定时器，每5秒执行一次
      this.pollingInterval = setInterval(async () => {
        if (this.isPolling) {
          await this.performPollingAnalysis();
        }
      }, 5000); // 5秒
      
      console.log('前端轮询已启动，每5秒执行一次');
    },
    
    async performPollingAnalysis() {
      try {
        console.log('轮询分析开始，当前页面时间:', this.currentTime);
        
        // 构建请求数据，只传group_id
        const requestData = {
          group_id: this.selectedGroupId
        };
        
        // 并行调用三个接口
        const [anomalyResult, aiHistoryResult, nextNotifyResult] = await Promise.all([
          apiService.getAnomalyStatus(requestData),           // 本地分析数据
          apiService.getAiAnalyze(requestData),               // 最近3条AI提示
          apiService.getNextNotifyAiAnalyzeResult(requestData) // 即将推送的AI提示
        ]);
        
        console.log('轮询分析结果:', anomalyResult);
        console.log('AI提示历史结果:', aiHistoryResult);
        console.log('即将推送结果:', nextNotifyResult);
        console.log('轮询分析结束，当前页面时间:', this.currentTime);
        
        // 处理本地分析数据（最近3轮）
        if (anomalyResult && Array.isArray(anomalyResult) && anomalyResult.length > 0) {
          console.log('收到最近3轮分析数据:', anomalyResult);
          
          // 检查第一条数据的时间范围是否发生变化
          const firstRoundData = anomalyResult[0];
          const currentTimeRange = firstRoundData.time_range;
          
          // 比较时间范围是否发生变化
          const timeRangeChanged = this.hasTimeRangeChanged(currentTimeRange);
          
          if (timeRangeChanged) {
            console.log('时间范围发生变化，更新页面数据');
            
            // 处理每一轮的数据
            anomalyResult.forEach((roundData, roundIndex) => {
              const roundNumber = anomalyResult.length - roundIndex; // 最新的轮次为第1轮
              
              // 提取时间范围
              const timeRange = roundData.time_range;
              const roundStartTime = timeRange ? timeRange.start : null;
              
              // 提取用户分析数据（排除time_range字段）
              const userAnalysisData = {};
              Object.keys(roundData).forEach(key => {
                if (key !== 'time_range') {
                  userAnalysisData[key] = roundData[key];
                }
              });
              
              // 更新用户卡片显示分析结果
              this.updateUserCardsWithAnalysis(userAnalysisData, roundStartTime, roundNumber);
            });
            
            // 更新记录的时间范围
            this.lastTimeRange = currentTimeRange;
          } else {
            console.log('时间范围未变化，跳过页面更新');
          }
        } else {
          console.log('轮询分析完成，但无历史数据');
        }
        
        // 处理AI提示历史数据（最近3轮）
        if (aiHistoryResult && Array.isArray(aiHistoryResult) && aiHistoryResult.length > 0) {
          console.log('收到最近3轮AI分析数据:', aiHistoryResult);
          
          // 检查第一条数据的时间范围是否发生变化
          const firstRoundData = aiHistoryResult[0];
          const currentAiTimeRange = firstRoundData.time_range;
          
          // 比较时间范围是否发生变化
          const aiTimeRangeChanged = this.hasAiTimeRangeChanged(currentAiTimeRange);
          
          if (aiTimeRangeChanged) {
            console.log('AI分析时间范围发生变化，更新AI提示数据');
            
            // 处理每一轮的AI分析数据
            aiHistoryResult.forEach((roundData, roundIndex) => {
              const roundNumber = aiHistoryResult.length - roundIndex; // 最新的轮次为第1轮
              
              // 提取时间范围
              const timeRange = roundData.time_range;
              const roundStartTime = timeRange ? timeRange.start : null;
              
              // 提取用户AI分析数据（排除time_range字段）
              const userAiData = {};
              Object.keys(roundData).forEach(key => {
                if (key !== 'time_range') {
                  userAiData[key] = roundData[key];
                }
              });
              
              // 更新用户AI提示数据
              this.updateUserAiHistoryData(userAiData, roundStartTime, roundNumber);
            });
            
            // 更新记录的AI时间范围
            this.lastAiTimeRange = currentAiTimeRange;
          } else {
            console.log('AI分析时间范围未变化，跳过AI提示更新');
          }
        }
        
        // 处理即将推送的AI提示数据
        if (nextNotifyResult && typeof nextNotifyResult === 'object') {
          console.log('收到即将推送的AI提示数据:', nextNotifyResult);
          
          // 检查是否需要更新数据
          const shouldUpdate = this.shouldUpdateNextNotifyData(nextNotifyResult);
          
          if (shouldUpdate) {
            console.log('需要更新即将推送数据');
            
            // 清除所有现有的倒计时
            this.clearAllCountdowns();
            
            // 更新即将推送的AI提示数据
            this.updateNextNotifyData(nextNotifyResult);
            
            // 更新记录的时间范围和时间
            this.lastNextNotifyTimeRange = nextNotifyResult.time_range;
            this.lastNextNotifyTime = this.extractNextNotifyTime(nextNotifyResult);
          } else {
            console.log('无需更新即将推送数据');
          }
        }
      } catch (error) {
        console.error('轮询分析失败:', error);
      }
    },
    async stopPollingAnalysis() {
      if (!this.isPolling) return;
      
      try {
        console.log('停止前端轮询分析...');
        
        // 清除轮询定时器
        if (this.pollingInterval) {
          clearInterval(this.pollingInterval);
          this.pollingInterval = null;
        }
        
        // 停止时间更新
        this.stopTimeUpdate();
        
        this.isPolling = false;
        console.log('前端轮询已停止');
        alert('前端轮询已停止');
      } catch (error) {
        console.error('停止轮询失败:', error);
        alert('停止轮询失败：' + (error.message || '未知错误'));
      }
    },

  },
  async mounted() {
    await this.fetchAllUsers();
    await this.fetchGroups();
    
    // 初始化时间范围：2025年7月10日下午3点（本地时间）
    const year = 2025;
    const month = 7; // 7月
    const day = 10;
    const startHour = 15; // 下午3点
    const startMinute = 2; // 15:02
    const endHour = 15; // 下午3点
    const endMinute = 4; // 15:04
    
    // 创建本地时间，避免时区转换问题
    const startTime = new Date(year, month - 1, day, startHour, startMinute);
    const endTime = new Date(year, month - 1, day, endHour, endMinute);
    
    // 格式化为本地时间字符串，格式：YYYY-MM-DDTHH:MM
    const formatLocalTime = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };
    
    this.startTime = formatLocalTime(startTime);
    this.endTime = formatLocalTime(endTime);
    
    // 初始化当前时间选择器
    console.log('初始化时间选择器，UTC时间:', this.currentTime);
    this.currentTimeLocal = this.convertUtcToLocal(this.currentTime);
    console.log('转换后的本地时间:', this.currentTimeLocal);
  },
  beforeUnmount() {
    // 组件销毁前清除定时器
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    // 停止时间更新
    this.stopTimeUpdate();
    // 清除所有倒计时
    this.clearAllCountdowns();
  }
}
</script>

<style scoped>
.admin-judge-root {
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f5f6fa 0%, #e9ebf0 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
}
.controls-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20px;
  padding: 10px;
  width: 100%;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-left: 20px;
}
.group-selector {
  margin-top: 0;
  margin-bottom: 0;
  font-size: 1rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}
.group-selector select {
  font-size: 1rem;
  padding: 6px 10px;
  border: 1px solid #d0d5db;
  background: #fff;
  outline: none;
  transition: border 0.2s;
  min-width: 120px;
  border-radius:6px

}
.group-selector select:focus {
  border: 1.5px solid #1976d2;
}
.time-selector {
  margin-top: 0;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
  justify-content: center;
}
.time-input-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}
.time-input-group label {
  font-weight: 500;
  color: #333;
  font-size: 1rem;
  white-space: nowrap;
}
.time-input {
  font-size: 1rem;
  padding: 6px 10px;
  border: 1px solid #d0d5db;
  background: #fff;
  outline: none;
  transition: border 0.2s;
  min-width: 140px;
  max-width: 200px;
  border-radius:6px

}
.time-input:focus {
  border: 1.5px solid #1976d2;
}
.analyze-btn {
  background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
  font-size: 1rem;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px 0 rgba(76,175,80,0.12);
  min-width: 80px;
  white-space: nowrap;
}
.analyze-btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #5cb85c 0%, #4cae4c 100%);
  box-shadow: 0 3px 12px 0 rgba(76,175,80,0.18);
  transform: translateY(-1px);
}
.analyze-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  color: #888;
  transform: none;
  box-shadow: none;
}
.polling-btn {
  background: linear-gradient(90deg, #2196F3 0%, #1976D2 100%);
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
  font-size: 1rem;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px 0 rgba(33,150,243,0.12);
  min-width: 80px;
  white-space: nowrap;
}
.polling-btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #42a5f5 0%, #2196f3 100%);
  box-shadow: 0 3px 12px 0 rgba(33,150,243,0.18);
  transform: translateY(-1px);
}
.polling-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  color: #888;
  transform: none;
  box-shadow: none;
}
.stop-polling-btn {
  background: linear-gradient(90deg, #f44336 0%, #d32f2f 100%);
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
  font-size: 1rem;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px 0 rgba(244,67,54,0.12);
  min-width: 80px;
  white-space: nowrap;
}
.stop-polling-btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #ef5350 0%, #f44336 100%);
  box-shadow: 0 3px 12px 0 rgba(244,67,54,0.18);
  transform: translateY(-1px);
}
.stop-polling-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  color: #888;
  transform: none;
  box-shadow: none;
}

.current-time-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #495057;
}

.time-label {
  font-weight: 500;
  color: #6c757d;
  white-space: nowrap;
}

.time-picker {
  font-size: 0.85rem;
  padding: 4px 8px;
  border: 1px solid #d0d5db;
  border-radius: 4px;
  background: #fff;
  outline: none;
  transition: border 0.2s;
  font-family: 'Courier New', monospace;
}

.time-picker:focus {
  border: 1.5px solid #1976d2;
}

.time-utc {
  font-weight: 600;
  color: #007bff;
  background: rgba(0, 123, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
}

.group-title {
  margin-top: 10px;
  margin-bottom: 12px;
  font-size: 1.6rem;
  font-weight: 700;
  color: #222;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, 'San Francisco', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}
.user-cards {
  display: flex;
  gap: 20px;
  justify-content: center;
  width: 100%;
  flex-wrap: wrap;
}
.user-card {
  width: 28vw;
  min-width: 220px;
  max-width: 480px;
  background: rgba(255,255,255,0.85);
  border-radius: 24px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.08);
  padding: 20px 25px;
  min-height: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: box-shadow 0.2s;
}
.user-card:hover {
  box-shadow: 0 8px 32px 0 rgba(0,0,0,0.12);
}
.user-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #222;
  background: #f0f4fa;
  border-radius: 8px;
  padding: 8px 0;
  width: 100%;
  text-align: center;
  border: 2px solid transparent;
  transition: border 0.2s;
}
.user-info {
  background: #f5f6fa;
  border-radius: 8px;
  width: 100%;
  text-align: center;
  margin-bottom: 15px;
  padding: 10px 0;
  font-size: 1.1rem;
  color: #444;
}
.ai-tip {
  background: #e3f0ff;
  border-radius: 8px;
  width: 100%;
  text-align: center;
  margin-bottom: 20px;
  padding: 12px 0;
  font-weight: 600;
  color: #1976d2;
  font-size: 1.1rem;
}
.cancel-send-btn {
  background: linear-gradient(90deg, #dc3545 0%, #c82333 100%);
  border: none;
  border-radius: 6px;
  width: 50%;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 0.8rem;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px 0 rgba(220,53,69,0.12);
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cancel-send-btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #e74c3c 0%, #dc3545 100%);
  box-shadow: 0 4px 16px 0 rgba(220,53,69,0.18);
  transform: translateY(-1px);
}
.cancel-send-btn:disabled {
  background: #6c757d;
  color: #adb5bd;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.countdown-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.immediate-push-btn {
  background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 0.8rem;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px 0 rgba(40,167,69,0.12);
  flex: 1;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.immediate-push-btn:hover {
  background: linear-gradient(90deg, #20c997 0%, #28a745 100%);
  box-shadow: 0 3px 12px 0 rgba(40,167,69,0.18);
  transform: translateY(-1px);
}

.pushed-status {
  text-align: center;
  padding: 8px;
  background: rgba(40, 167, 69, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(40, 167, 69, 0.2);
}

.pushed-label {
  color: #28a745;
  font-weight: 600;
  font-size: 0.9rem;
}

.push-status {
  text-align: center;
  padding: 8px;
  background: rgba(40, 167, 69, 0.1);
  border-radius: 6px;
  margin-top: 8px;
}

.status-text {
  color: #28a745;
  font-weight: 600;
  font-size: 0.9rem;
}

/* 立即推送模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.immediate-push-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 100vh;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e9ecef;
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
  font-weight: 600;
}

.modal-body {
  padding: 20px 24px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #495057;
  font-weight: 600;
  font-size: 0.85rem;
}

.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d0d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: none;
  min-height: 80px;
  max-height: 150px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e9ecef;
  justify-content: flex-end;
  flex-shrink: 0;
}

.confirm-btn {
  background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  font-size: 0.9rem;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px 0 rgba(40,167,69,0.12);
}

.confirm-btn:hover {
  background: linear-gradient(90deg, #20c997 0%, #28a745 100%);
  box-shadow: 0 4px 16px 0 rgba(40,167,69,0.18);
  transform: translateY(-1px);
}

.cancel-btn {
  background: #6c757d;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  font-size: 0.9rem;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.no-push-status {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  width: 100%;
  padding: 12px 0;
  text-align: center;
  font-size: 1rem;
  color: #6c757d;
  font-weight: 500;
}

/* 分析结果样式 */
.analysis-results {
  width: 100%;
  margin-bottom: 10px;
}

.analysis-section {
  margin-bottom: 6px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #e9ecef;
}

.analysis-section.total-section {
  background: #e8f5e8;
  border-left-color: #28a745;
}

.section-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 6px;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.total-section .section-title {
  color: #155724;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  font-size: 0.85rem;
}

.analysis-item:last-child {
  margin-bottom: 0;
}

.analysis-item .label {
  font-weight: 500;
  color: #555;
}

.analysis-item .value {
  font-weight: 600;
  color: #333;
}

/* 紧凑数据网格样式 */
.compact-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
  gap: 4px;
  margin-top: 6px;
}

.data-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3px 4px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 3px;
  font-size: 0.7rem;
  text-align: center;
}

.data-label {
  font-weight: 500;
  color: #666;
  margin-bottom: 1px;
  font-size: 0.65rem;
}

.data-value {
  font-weight: 600;
  color: #333;
  font-size: 0.75rem;
}

.total-score {
  font-size: 1rem;
  color: #155724;
  font-weight: 700;
}

.level-badge {
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.65rem;
  font-weight: 600;
  text-align: center;
  min-width: 50px;
}

.total-level {
  font-size: 0.7rem;
  padding: 3px 6px;
  min-width: 70px;
}

.level-no {
  background: #ffebee;
  color: #c62828;
}

.level-low {
  background: #fff3e0;
  color: #ef6c00;
}

.level-normal {
  background: #e8f5e8;
  color: #2e7d32;
}

.level-high {
  background: #e3f2fd;
  color: #1565c0;
}

.level-dominant {
  background: #f3e5f5;
  color: #7b1fa2;
}

.no-analysis {
  width: 100%;
  margin-bottom: 20px;
}

/* 轮次标签 */
.round-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.round-tab {
  padding: 4px 10px;
  background: #e9ecef;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  user-select: none;
}

.round-tab:hover {
  background: #dee2e6;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.round-tab.active {
  background: #007bff;
  color: white;
  border-color: #0056b3;
  box-shadow: 0 2px 6px rgba(0,123,255,0.3);
}

/* 进度条样式 */

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.progress-value {
  color: #007bff;
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.speech-fill {
  background: linear-gradient(90deg, #28a745, #20c997);
}

.note-fill {
  background: linear-gradient(90deg, #ffc107, #fd7e14);
}

.browser-fill {
  background: linear-gradient(90deg, #17a2b8, #6f42c1);
}

.total-fill {
  background: linear-gradient(90deg, #007bff, #6610f2);
}

/* 历史对比 */
.history-comparison {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #6c757d;
}

.history-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: white;
  border-radius: 6px;
}

.history-round {
  font-weight: 600;
  color: #495057;
  min-width: 60px;
  font-size: 0.8rem;
}

.history-scores {
  display: flex;
  gap: 16px;
  flex: 1;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.score-label {
  font-size: 0.7rem;
  color: #6c757d;
  font-weight: 500;
}

.mini-progress {
  width: 100%;
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* AI提示区域样式 */
.ai-suggestions-section {
  width: 100%;
  margin-bottom: 12px;
}

.ai-history-section,
.ai-current-section {
  margin-bottom: 8px;
}

.ai-history-section {
  background: #f8f9fa;
  border-left-color: #6c757d;
}

.ai-current-section {
  background: #e8f5e8;
  border-left-color: #28a745;
}

.ai-history-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ai-history-item,
.ai-current-item {
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.8rem;
  margin-bottom: 3px;
}

.ai-history-item:hover,
.ai-current-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(1px);
}

.ai-current-item {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(40, 167, 69, 0.2);
}

.ai-summary {
  color: #495057;
  margin-bottom: 1px;
  line-height: 1.2;
  font-weight: 500;
}

.ai-time {
  color: #6c757d;
  font-size: 0.7rem;
  font-weight: 400;
}

.no-ai-history {
  padding: 4px 6px;
  text-align: center;
  color: #6c757d;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 3px;
}

.no-ai-current {
  padding: 4px 6px;
  text-align: center;
  color: #6c757d;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 3px;
}

.countdown-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.countdown-label {
  font-size: 0.85rem;
  color: #495057;
  font-weight: 600;
}

.countdown-time {
  font-size: 1.1rem;
  font-weight: 700;
  color: #28a745;
  font-family: 'Courier New', monospace;
  background: rgba(40, 167, 69, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 60px;
  text-align: center;
}

.countdown-time.urgent {
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
  animation: pulse 1s infinite;
  font-weight: 800;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}



/* AI详情弹窗样式 */
.ai-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.ai-detail-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.ai-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.ai-detail-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e9ecef;
  color: #333;
}

.ai-detail-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  color: #495057;
  font-size: 0.9rem;
  font-weight: 600;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 4px;
}

.detail-section p {
  margin: 4px 0;
  font-size: 0.85rem;
  line-height: 1.4;
  color: #333;
}

.glasses-summary {
  background: #e3f2fd;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
  font-weight: 500;
}

.evidence-text {
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  line-height: 1.4;
  white-space: pre-wrap;
  color: #495057;
  border: 1px solid #e9ecef;
}

.distribution-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.stat-item {
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #495057;
}
</style> 