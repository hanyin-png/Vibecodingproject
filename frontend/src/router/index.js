// 路由配置：首页仪表盘 + 6 个功能页面
import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../pages/Dashboard.vue'
import Equipment from '../pages/Equipment.vue'
import Monitor from '../pages/Monitor.vue'
import Predict from '../pages/Predict.vue'
import Alarms from '../pages/Alarms.vue'
import Diagnose from '../pages/Diagnose.vue'
import Workorders from '../pages/Workorders.vue'

const routes = [
  { path: '/', component: Dashboard },
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
