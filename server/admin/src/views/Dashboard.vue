<template>
  <el-container>
    <el-aside width="250px">
      <el-menu :default-openeds="['1', '2', '3', '4', '5', '6']">
        <el-sub-menu index="1">
          <template #title
            ><el-icon><User /></el-icon>用户管理</template
          >
          <el-menu-item v-for="api in apiCategories[0].apis" :key="api.url">
            <el-icon><UserFilled /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="2">
          <template #title
            ><el-icon><Menu /></el-icon>小组管理</template
          >
          <el-menu-item v-for="api in apiCategories[1].apis" :key="api.url">
            <el-icon><Menu /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="3">
          <template #title
            ><el-icon><ChatDotRound /></el-icon>聊天管理</template
          >
          <el-menu-item v-for="api in apiCategories[2].apis" :key="api.url">
            <el-icon><ChatDotRound /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="4">
          <template #title
            ><el-icon><Cpu /></el-icon>AI 机器人</template
          >
          <el-menu-item v-for="api in apiCategories[3].apis" :key="api.url">
            <el-icon><Cpu /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="5">
          <template #title
            ><el-icon><ChatDotRound /></el-icon>聊天议程与汇总</template
          >
          <el-menu-item v-for="api in apiCategories[4].apis" :key="api.url">
            <el-icon><ChatDotRound /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="6">
          <template #title
            ><el-icon><Setting /></el-icon>讨论核心与反馈</template
          >
          <el-menu-item v-for="api in apiCategories[5].apis" :key="api.url">
            <el-icon><Setting /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div>后台管理面板</div>
      </el-header>
      <el-main>
        <el-card class="dashboard-card">
          <h2>API 测试</h2>
          <div v-for="(category, index) in apiCategories" :key="index">
            <el-divider>{{ category.category }}</el-divider>
            <div class="api-buttons">
              <ApiButton
                v-for="api in category.apis"
                :key="api.url"
                :apiUrl="api.url"
                :label="api.name"
              />
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from "vue";
import {
  Menu,
  User,
  UserFilled,
  ChatDotRound,
  Cpu,
  Setting,
} from "@element-plus/icons-vue";
import ApiButton from "../components/ApiButton.vue";

const apiCategories = ref([
  {
    category: "用户管理 API",
    apis: [
      { name: "获取所有用户", url: "http://localhost:8000/api/users" },
      {
        name: "获取单个用户",
        url: "http://localhost:8000/api/users/{user_id}",
      },
    ],
  },
  {
    category: "小组管理 API",
    apis: [
      { name: "获取所有小组", url: "http://localhost:8000/api/groups" },
      {
        name: "获取单个小组",
        url: "http://localhost:8000/api/groups/{group_id}",
      },
      {
        name: "获取小组成员",
        url: "http://localhost:8000/api/groups/{group_id}/members",
      },
    ],
  },
  {
    category: "聊天 API",
    apis: [
      {
        name: "获取聊天记录",
        url: "http://localhost:8000/api/chat/{group_id}",
      },
      { name: "发送聊天消息", url: "http://localhost:8000/api/chat/send" },
    ],
  },
  {
    category: "AI 机器人 API",
    apis: [
      { name: "AI 生成回答", url: "http://localhost:8000/api/ai/respond" },
    ],
  },
  {
    category: "聊天议程与汇总 API",
    apis: [
      {
        name: "获取聊天议程",
        url: "http://localhost:8000/api/chat/agenda/{group_id}",
      },
      {
        name: "获取聊天汇总",
        url: "http://localhost:8000/api/chat/summary/{group_id}",
      },
    ],
  },
  {
    category: "讨论核心与反馈 API",
    apis: [
      {
        name: "获取讨论核心",
        url: "http://localhost:8000/api/discussion_core",
      },
      {
        name: "获取讨论反馈",
        url: "http://localhost:8000/api/engagement_feedback",
      },
      {
        name: "获取讨论见解",
        url: "http://localhost:8000/api/discussion_insights",
      },
      {
        name: "获取讨论术语",
        url: "http://localhost:8000/api/discussion_terms",
      },
    ],
  },
]);
</script>

<style scoped>
.el-container {
  height: 100vh;
}
.el-header {
  background: #f5f7fa;
  padding: 20px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
}
.el-main {
  padding: 20px;
}
.dashboard-card {
  padding: 20px;
}
.api-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}
</style>
