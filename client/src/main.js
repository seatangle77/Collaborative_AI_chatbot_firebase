import { createApp } from 'vue';
import App from './App.vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css'; // 引入样式
import router from './router'; // 如果有路由
import axios from 'axios';

const app = createApp(App);

app.use(ElementPlus);
app.use(router); // 如果有 Vue Router
app.config.globalProperties.$axios = axios;

app.mount('#app');