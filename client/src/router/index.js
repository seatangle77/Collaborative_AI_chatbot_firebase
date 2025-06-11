import { createRouter, createWebHashHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/public-display",
  },
  {
    path: "/personal-dashboard",
    name: "PersonalWorkspace",
    component: () => import("../views/PersonalWorkspace.vue"),
  },
  {
    path: "/public-display",
    name: "PublicScreen",
    component: () => import("../views/PublicScreen.vue"),
  },
  {
    path: "/admin",
    name: "AdminPage",
    component: () => import("../views/AdminPage.vue"),
  }
];

const router = createRouter({
  history: createWebHashHistory(), // ✅ 改成 Hash 模式，避免 307 问题
  routes,
});

export default router;