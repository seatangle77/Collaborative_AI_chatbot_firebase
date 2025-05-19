import { createRouter, createWebHashHistory } from "vue-router";
import ChatView from "../views/ChatView.vue";
import PersonalDashboard from "../personal_device/PersonalDashboard.vue";

const routes = [
  {
    path: "/",
    name: "Chat",
    component: ChatView,
  },
  {
    path: "/personal-dashboard",
    name: "PersonalDashboard",
    component: PersonalDashboard,
  },
  {
    path: "/meeting",
    name: "MeetingView",
    component: () => import("../views/MeetingView.vue"),
  }
];

const router = createRouter({
  history: createWebHashHistory(), // ✅ 改成 Hash 模式，避免 307 问题
  routes,
});

export default router;