<template>
  <div class="admin-judge-root">
    <div class="group-selector">
      <label for="group-select">选择小组：</label>
      <select id="group-select" v-model="selectedGroupId" @change="onGroupChange">
        <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
      </select>
    </div>
    <div class="group-title">{{ currentGroupName }}</div>
    <div class="user-cards">
      <div class="user-card" v-for="user in users" :key="user.id">
        <div class="user-name">{{ user.name }}</div>
        <div class="user-info">发言比例</div>
        <div class="user-info">行为数据比例</div>
        <div class="ai-tip">AI提示</div>
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
    }
  },
  async mounted() {
    await this.fetchAllUsers();
    await this.fetchGroups();
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
.group-selector {
  margin-top: 32px;
  margin-bottom: 8px;
  font-size: 1.1rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 12px;
}
.group-selector select {
  font-size: 1.1rem;
  padding: 6px 16px;
  border-radius: 8px;
  border: 1px solid #d0d5db;
  background: #fff;
  outline: none;
  transition: border 0.2s;
}
.group-selector select:focus {
  border: 1.5px solid #1976d2;
}
.group-title {
  margin-top: 16px;
  margin-bottom: 40px;
  font-size: 2.4rem;
  font-weight: 700;
  color: #222;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, 'San Francisco', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}
.user-cards {
  display: flex;
  gap: 40px;
  justify-content: center;
  width: 100%;
  flex-wrap: wrap;
}
.user-card {
  background: rgba(255,255,255,0.85);
  border-radius: 24px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.08);
  padding: 40px 36px;
  width: 440px;
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
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 20px;
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
  margin-bottom: 16px;
  padding: 12px 0;
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
</style> 