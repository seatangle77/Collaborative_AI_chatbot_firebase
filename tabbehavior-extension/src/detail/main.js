import { createApp } from 'vue';
import DetailApp from './DetailApp.vue';

// 新增导入 Element Plus 和样式
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

const app = createApp(DetailApp);

app.use(ElementPlus);

app.mount('#app');