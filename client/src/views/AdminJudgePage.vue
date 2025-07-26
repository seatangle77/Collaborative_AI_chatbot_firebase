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
        <div class="polling-time-group">
          <label for="polling-start-time">轮询开始时间：</label>
          <input 
            id="polling-start-time" 
            type="datetime-local" 
            v-model="pollingStartTime" 
            class="time-input"
          />
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
              :class="{ active: index === 0 }"
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
                  <span class="progress-value">{{ user.analysis.speech_percent }}</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill speech-fill" 
                    :style="{ width: parseFloat(user.analysis.speech_percent) + '%' }"
                  ></div>
                </div>
                <div class="analysis-item">
                  <span class="label">发言时长：</span>
                  <span class="value">{{ user.analysis.speech_duration }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">发言等级：</span>
                  <span class="value level-badge" :class="getSpeechLevelClass(user.analysis.speech_level)">
                    {{ user.analysis.speech_level }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 笔记编辑数据 -->
            <div class="analysis-section">
              <div class="section-title">笔记编辑</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>编辑活跃度</span>
                  <span class="progress-value">{{ user.analysis.note_edit_score * 100 }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill note-fill" 
                    :style="{ width: user.analysis.note_edit_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="analysis-item">
                  <span class="label">编辑次数：</span>
                  <span class="value">{{ user.analysis.note_edit_count }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">字符数：</span>
                  <span class="value">{{ user.analysis.note_edit_char_count }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">编辑等级：</span>
                  <span class="value level-badge" :class="getNoteLevelClass(user.analysis.note_edit_level)">
                    {{ user.analysis.note_edit_level }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 浏览行为数据 -->
            <div class="analysis-section">
              <div class="section-title">浏览行为</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>浏览活跃度</span>
                  <span class="progress-value">{{ user.analysis.browser_score * 100 }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill browser-fill" 
                    :style="{ width: user.analysis.browser_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="analysis-item">
                  <span class="label">页面数：</span>
                  <span class="value">{{ user.analysis.page_count }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">鼠标操作：</span>
                  <span class="value">{{ user.analysis.mouse_action_count }}次</span>
                </div>
                <div class="analysis-item">
                  <span class="label">浏览时长：</span>
                  <span class="value">{{ user.analysis.mouse_duration }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">浏览比例：</span>
                  <span class="value">{{ user.analysis.mouse_percent }}</span>
                </div>
                <div class="analysis-item">
                  <span class="label">浏览等级：</span>
                  <span class="value level-badge" :class="getBrowserLevelClass(user.analysis.browser_level)">
                    {{ user.analysis.browser_level }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 总体评估 -->
            <div class="analysis-section total-section">
              <div class="section-title">总体评估</div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>总参与度</span>
                  <span class="progress-value">{{ (user.analysis.total_score * 100).toFixed(1) }}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill total-fill" 
                    :style="{ width: user.analysis.total_score * 100 + '%' }"
                  ></div>
                </div>
                <div class="analysis-item">
                  <span class="label">参与等级：</span>
                  <span class="value level-badge total-level" :class="getLevelClass(user.analysis.total_level)">
                    {{ user.analysis.total_level }}
                  </span>
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
        
        <button class="send-btn">取消发送（5秒后自动发送）</button>
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
      pollingStartTime: '',
      isAnalyzing: false,
      isPolling: false,
      pollingInterval: null, // 存储定时器ID
      currentPollingStartTime: '', // 当前轮询的起始时间
      analysisHistory: {}, // 存储每个用户的历史分析数据 {userId: [{round1}, {round2}, {round3}]}
      currentRound: 1, // 当前轮次
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
          name: userInfo ? userInfo.name : (member.name || '未知用户')
        };
      });
    },
    async onGroupChange() {
      await this.fetchGroupMembers(this.selectedGroupId);
    },
    updateUserCardsWithAnalysis(analysisResult, roundStartTime) {
      // 更新用户卡片显示分析结果，并保存历史数据
      this.users = this.users.map(user => {
        const userAnalysis = analysisResult[user.id];
        if (userAnalysis) {
          // 保存到历史记录
          if (!this.analysisHistory[user.id]) {
            this.analysisHistory[user.id] = [];
          }
          // 添加轮次信息
          const analysisWithRound = {
            ...userAnalysis,
            round: this.currentRound,
            timestamp: Date.now(),
            start_time: roundStartTime // 新增
          };
          // 添加到历史记录开头（最新的在前面）
          this.analysisHistory[user.id].unshift(analysisWithRound);
          // 只保留最新3轮
          if (this.analysisHistory[user.id].length > 3) {
            this.analysisHistory[user.id] = this.analysisHistory[user.id].slice(0, 3);
          }
          return {
            ...user,
            analysis: userAnalysis,
            analysisHistory: this.analysisHistory[user.id]
          };
        }
        return user;
      });
      // 轮次递增
      this.currentRound++;
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
          
          // 更新用户卡片显示分析结果
          const roundStartTime = result.raw_data_summary?.time_range?.start;
          this.updateUserCardsWithAnalysis(result.local_analysis, roundStartTime);
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
      
      if (!this.pollingStartTime) {
        alert('请选择轮询开始时间');
        return;
      }
      
      if (new Date(this.startTime) >= new Date(this.endTime)) {
        alert('开始时间必须早于结束时间');
        return;
      }
      
      this.isPolling = true;
      // 初始化当前轮询起始时间
      this.currentPollingStartTime = this.pollingStartTime;
      // 立即执行一次分析
      await this.performPollingAnalysis();
      // 设置定时器，每1分钟执行一次
      this.pollingInterval = setInterval(async () => {
        if (this.isPolling) {
          await this.performPollingAnalysis();
        }
      }, 60000); // 1分钟
      
      console.log('前端轮询已启动，每1分钟执行一次');
    },
    
    async performPollingAnalysis() {
      try {
        // 计算本次的start_time和end_time
        const startTimeDate = new Date(this.currentPollingStartTime);
        const endTimeDate = new Date(startTimeDate.getTime() + 60 * 1000); // +1分钟
        const startTimeISO = startTimeDate.toISOString().slice(0, 19);
        const endTimeISO = endTimeDate.toISOString().slice(0, 19);
        // 构建请求数据
        const requestData = {
          group_id: this.selectedGroupId,
          round_index: 1,
          start_time: startTimeISO,
          end_time: endTimeISO,
          members: this.users.map(user => ({
            id: user.id,
            name: user.name
          }))
        };
        // 调用接口获取分析结果
        const result = await apiService.getAnomalyStatus(requestData);
        console.log('轮询分析结果:', result, '窗口:', startTimeISO, '->', endTimeISO);
        // 处理轮询分析结果
        if (result.local && result.local.length > 0) {
          // 获取最新的分析结果
          const latestAnalysis = result.local[result.local.length - 1];
          const timeKey = Object.keys(latestAnalysis)[0];
          const analysisData = latestAnalysis[timeKey];
          // 更新用户卡片显示分析结果
          this.updateUserCardsWithAnalysis(analysisData, timeKey);
        } else {
          console.log('轮询分析完成，但无历史数据');
        }
        // 推进到下一个时间窗口
        this.currentPollingStartTime = endTimeISO;
      } catch (error) {
        console.error('轮询分析失败:', error);
      }
    },
    async stopPollingAnalysis() {
      if (!this.isPolling) return;
      
      try {
        console.log('停止前端轮询分析...');
        
        // 清除定时器
        if (this.pollingInterval) {
          clearInterval(this.pollingInterval);
          this.pollingInterval = null;
        }
        
        this.isPolling = false;
        console.log('前端轮询已停止');
        alert('前端轮询已停止');
      } catch (error) {
        console.error('停止轮询失败:', error);
        alert('停止轮询失败：' + (error.message || '未知错误'));
      }
    }
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
    this.pollingStartTime = formatLocalTime(startTime);
  },
  beforeUnmount() {
    // 组件销毁前清除定时器
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
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
.polling-time-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}
.polling-time-group label {
  font-weight: 500;
  color: #333;
  font-size: 1rem;
  white-space: nowrap;
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
  min-height: 420px;
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
.send-btn {
  background: linear-gradient(90deg, #ffd580 0%, #ffc266 100%);
  border: none;
  border-radius: 8px;
  width: 100%;
  padding: 12px 0;
  font-weight: 600;
  font-size: 1.05rem;
  color: #7c4d00;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px 0 rgba(255,194,102,0.12);
}
.send-btn:hover {
  background: linear-gradient(90deg, #ffe0a3 0%, #ffd580 100%);
  box-shadow: 0 4px 16px 0 rgba(255,194,102,0.18);
}

/* 分析结果样式 */
.analysis-results {
  width: 100%;
  margin-bottom: 10px;
}

.analysis-section {
  margin-bottom: 8px;
  padding: 12px;
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
  margin-bottom: 8px;
  font-size: 0.9rem;
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

.total-score {
  font-size: 1rem;
  color: #155724;
  font-weight: 700;
}

.level-badge {
  padding: 3px 6px;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  min-width: 60px;
}

.total-level {
  font-size: 0.8rem;
  padding: 4px 8px;
  min-width: 80px;
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
  gap: 8px;
  margin-bottom: 8px;
}

.round-tab {
  padding: 6px 12px;
  background: #e9ecef;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
}

.round-tab.active {
  background: #007bff;
  color: white;
}

/* 进度条样式 */

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.progress-value {
  color: #007bff;
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
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
</style> 