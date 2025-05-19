// main.js
import { createApp } from 'vue'
import App from './App.vue'

// 引入 Element Plus 组件库
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入 Element Plus 的样式

const app = createApp(App)

app.use(ElementPlus)  // 使用 Element Plus

app.mount('#app')