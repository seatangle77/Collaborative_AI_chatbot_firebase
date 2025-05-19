import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import fs from 'fs';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 3000, // ✅ 这里是你的前端端口
    https: {
      key: fs.readFileSync('./local.dev-key.pem'),
      cert: fs.readFileSync('./local.dev.pem'),
    },
    proxy: {
      "/api": {
        target: "https://10.4.131.51:8000", // ✅ 改为电脑的局域网 IP
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});