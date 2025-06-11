import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import PopupApp from './PopupApp.vue'

createApp(PopupApp).use(ElementPlus).mount('#app')
