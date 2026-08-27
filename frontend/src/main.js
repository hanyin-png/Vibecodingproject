import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

// 注册 Element Plus 组件库
createApp(App).use(ElementPlus).mount('#app')
