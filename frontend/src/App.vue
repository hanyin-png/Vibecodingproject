<script setup>
// 整体布局：左侧导航 + 右侧内容区（router-view 显示当前页面）
const menus = [
  { path: '/equipment', title: '设备台账' },
  { path: '/monitor', title: '数据监测' },
  { path: '/predict', title: '健康评估' },
  { path: '/alarms', title: '预警中心' },
  { path: '/diagnose', title: '智能诊断' },
  { path: '/workorders', title: '维修工单' },
]
</script>

<template>
  <el-container class="layout">
    <el-aside width="200px">
      <div class="logo">设备智能运维平台</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          {{ m.title }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.logo {
  padding: 18px 16px;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
}
.el-aside {
  border-right: 1px solid #e4e7ed;
}
.el-menu {
  border-right: none;
}
</style>
