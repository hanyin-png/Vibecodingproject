<script setup>
import { ref } from 'vue'
import api from './api'

// 后端返回的内容，先给个初始提示
const message = ref('还没请求后端，点下面按钮试试')

async function testHello() {
  try {
    const resp = await api.get('/hello')
    message.value = resp.data.message + '（来自 ' + resp.data.project + '）'
  } catch (err) {
    message.value = '请求失败：' + err.message + '（后端启动了吗？）'
  }
}
</script>

<template>
  <div class="page">
    <h1>工业设备智能运维与预测性维护平台</h1>
    <p>前后端联通验证：{{ message }}</p>
    <el-button type="primary" @click="testHello">测试后端联通</el-button>
  </div>
</template>

<style scoped>
.page {
  max-width: 640px;
  margin: 60px auto;
  text-align: center;
}

.page h1 {
  font-size: 28px;
  line-height: 1.4;
}
</style>
