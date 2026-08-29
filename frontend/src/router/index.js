// 路由配置：6 个页面对应 6 个功能模块
import { createRouter, createWebHistory } from 'vue-router'

import Equipment from '../pages/Equipment.vue'
import Monitor from '../pages/Monitor.vue'
import Predict from '../pages/Predict.vue'
import Alarms from '../pages/Alarms.vue'
import Diagnose from '../pages/Diagnose.vue'
import Workorders from '../pages/Workorders.vue'

const routes = [
  { path: '/', redirect: '/equipment' },
  { path: '/equipment', component: Equipment },
  { path: '/monitor', component: Monitor },
  { path: '/predict', component: Predict },
  { path: '/alarms', component: Alarms },
  { path: '/diagnose', component: Diagnose },
  { path: '/workorders', component: Workorders },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
