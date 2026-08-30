<script setup>
// 首页总览（仪表盘）：统计卡片 + 健康状态分布饼图 + 健康度最低 TOP5
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

const stats = ref(null)
const batchLoading = ref(false)  // 批量评估按钮的加载状态
let pieChart = null

// 一键批量评估：全机群体检，完成后刷新统计
async function runBatch() {
  batchLoading.value = true
  try {
    // 批量要跑几秒，单独把这个请求的超时放宽到 60 秒（全局默认 5 秒不够）
    const resp = await api.post('/predict/batch', null, { timeout: 60000 })
    ElMessage.success(`${resp.data.message}：评估 ${resp.data.evaluated} 台，新增预警 ${resp.data.new_alarms} 条`)
    location.reload()  // 重新加载统计数据（饼图要重建，直接刷新最稳妥）
  } catch (err) {
    ElMessage.error('批量评估失败：' + err.message)
  } finally {
    batchLoading.value = false
  }
}

function scoreColor(score) {
  if (score > 60) return '#67c23a'
  if (score > 30) return '#e6a23c'
  return '#f56c6c'
}

onMounted(async () => {
  const resp = await api.get('/stats')
  stats.value = resp.data
  await nextTick()  // 等 v-if 把饼图容器渲染出来，再初始化 ECharts

  // 健康状态分布饼图（固定 健康→预警→故障 的顺序，保证颜色和语义对上）
  const ORDER = ['健康', '预警', '故障']
  const dist = ORDER.map(s => stats.value.status_dist.find(d => d.status === s))
    .filter(Boolean)
    .map(d => ({ name: d.status, value: d.count }))
  pieChart = echarts.init(document.getElementById('pie'))
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    color: ['#67c23a', '#e6a23c', '#f56c6c'],  // 健康绿 / 预警橙 / 故障红
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      label: { formatter: '{b}：{c} 台' },
      data: dist,
    }],
  })
})
</script>

<template>
  <div v-if="stats">
    <div class="header">
      <h2>首页总览</h2>
      <el-button type="primary" :loading="batchLoading" @click="runBatch">一键评估全部设备</el-button>
    </div>

    <!-- 三张统计卡 -->
    <div class="cards">
      <el-card class="card">
        <div class="num">{{ stats.equipment_total }}</div>
        <div class="label">设备总数（台）</div>
      </el-card>
      <el-card class="card">
        <div class="num" style="color:#e6a23c">{{ stats.alarm_open }}</div>
        <div class="label">未处理预警（条）</div>
      </el-card>
      <el-card class="card">
        <div class="num" style="color:#f56c6c">{{ stats.workorder_open }}</div>
        <div class="label">待处理工单（个）</div>
      </el-card>
    </div>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header><b>设备健康状态分布</b></template>
          <div id="pie" style="height: 320px"></div>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header><b>健康度最低 TOP 5（重点关注）</b></template>
          <el-table :data="stats.low_health_top5" stripe>
            <el-table-column prop="code" label="设备编号" width="140" />
            <el-table-column label="健康度" width="120">
              <template #default="{ row }">
                <span :style="{ color: scoreColor(row.health_score), fontWeight: 'bold' }">
                  {{ row.health_score }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="rul" label="剩余寿命（循环）" />
          </el-table>
          <p class="tip">提示：到「健康评估」页对设备做评估后，这里才会出现数据。</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header h2 {
  margin: 0;
}
.cards {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.card {
  flex: 1;
  text-align: center;
}
.num {
  font-size: 40px;
  font-weight: bold;
}
.label {
  color: #909399;
  margin-top: 8px;
}
.tip {
  color: #909399;
  font-size: 12px;
  margin-bottom: 0;
}
</style>
