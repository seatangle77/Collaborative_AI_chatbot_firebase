import { createApp } from 'vue';
import App from './App.vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css'; // 引入样式
import 'quill/dist/quill.snow.css'; // 引入 Quill 样式
import router from './router'; // 如果有路由
import axios from 'axios';
// CKEditor 使用组件内按需引入，不在此处全局注册

const app = createApp(App);

app.use(ElementPlus);
app.use(router); // 如果有 Vue Router
app.config.globalProperties.$axios = axios;

app.mount('#app');