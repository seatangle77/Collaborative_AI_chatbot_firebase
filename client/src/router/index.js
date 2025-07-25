import { createRouter, createWebHashHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/public-display",
  },
  {
    path: "/personal-dashboard/:name",
    name: "PersonalWorkspace",
    component: () => import("../views/PersonalWorkspace.vue"),
  },
  {
    path: "/public-display/:name",
    name: "PublicScreen",
    component: () => import("../views/PublicScreen.vue"),
  },
  {
    path: "/admin",
    name: "AdminFirebasePage",
    component: () => import("../views/AdminFirebasePage.vue"),
  },
  {
    path: "/admin-judge",
    name: "AdminJudgePage",
    component: () => import("../views/AdminJudgePage.vue"),
  },
];

const router = createRouter({
  history: createWebHashHistory(), // ✅ 改成 Hash 模式，避免 307 问题
  routes,
});

export default router;