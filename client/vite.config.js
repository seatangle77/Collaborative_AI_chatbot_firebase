import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import fs from 'fs';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 3000, // ✅ 这里是你的前端端口
    // https: {
    // key: fs.readFileSync('./local.dev-key.pem'),
    //cert: fs.readFileSync('./local.dev.pem'),
    //},
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE, // ✅ 使用环境变量配置后端地址
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      '/analysis': 'http://localhost:8000', // 后端端口如有不同请修改
    },
  },
});