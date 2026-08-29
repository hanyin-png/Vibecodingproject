import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

// 注册 Element Plus 组件库和路由
createApp(App).use(ElementPlus).use(router).mount('#app')
