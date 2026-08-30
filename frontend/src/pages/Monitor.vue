<script setup>
// 数据监测页：选设备 -> ECharts 画关键传感器趋势曲线
// 支持按循环范围筛选；异常点（3σ 规则）用红点标出
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const equipmentList = ref([])   // 设备下拉框选项
const selectedId = ref(null)    // 选中的设备 id
const loading = ref(false)
const startCycle = ref(null)    // 循环范围筛选：起
const endCycle = ref(null)      // 循环范围筛选：止

// 展示的传感器：编号 -> 含义（都是 FD001 里有明显退化趋势的列）
const SENSORS = {
  s3: '高压压气机出口温度',
  s7: '高压压气机出口总压',
  s11: '高压压气机出口静压',
  s12: '燃油流量比值',
}

let chart = null  // ECharts 实例

async function loadEquipment() {
  const resp = await api.get('/equipment')
  equipmentList.value = resp.data
  if (resp.data.length > 0) {
    selectedId.value = resp.data[0].id  // 默认选第一台
  }
}

async function loadChart() {
  if (selectedId.value === null) return
  loading.value = true
  // 设备编号 ENG-001 -> unit 1
  const code = equipmentList.value.find(e => e.id === selectedId.value).code
  const unit = parseInt(code.split('-')[1])

  // 循环范围筛选：填了才传参
  const params = {}
  if (startCycle.value) params.start = startCycle.value
  if (endCycle.value) params.end = endCycle.value

  // 传感器数据 + 异常点（3σ 规则）两个接口一起查
  const [dataResp, abnormalResp] = await Promise.all([
    api.get(`/sensor/${unit}`, { params }),
    api.get(`/sensor/${unit}/abnormal-points`),
  ])
  const data = dataResp.data
  const abnormal = abnormalResp.data
  const valueOf = {}  // col -> {cycle: value}，标红点时查值用
  for (const col of Object.keys(SENSORS)) {
    valueOf[col] = Object.fromEntries(data.map(r => [r.cycle, r[col]]))
  }

  const cycles = data.map(r => r.cycle)
  const cols = Object.entries(SENSORS)
  // 2×2 子图布局：四个传感器量纲差太大，挤在一个坐标系里会看不清趋势
  const option = {
    tooltip: { trigger: 'axis' },
    grid: [
      { left: '8%', right: '55%', top: '12%', height: '30%' },
      { left: '58%', right: '5%', top: '12%', height: '30%' },
      { left: '8%', right: '55%', top: '60%', height: '30%' },
      { left: '58%', right: '5%', top: '60%', height: '30%' },
    ],
    xAxis: cols.map((_, i) => ({
      type: 'category', gridIndex: i, data: cycles, name: '循环数',
    })),
    yAxis: cols.map(([, name], i) => ({
      type: 'value', gridIndex: i, name, scale: true,
    })),
    series: cols.map(([col, name], i) => ({
      name,
      type: 'line',
      showSymbol: false,
      xAxisIndex: i,
      yAxisIndex: i,
      data: data.map(r => r[col]),
      // 异常点标红：只画筛选范围内存在的点（只显示红点，不带文字）
      markPoint: {
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#f56c6c' },
        label: { show: false },
        data: (abnormal[col] || [])
          .filter(c => c in valueOf[col])
          .map(c => ({ coord: [String(c), valueOf[col][c]], value: '异常' })),
      },
    })),
  }
  chart.setOption(option, true)  // true = 清空旧配置重画
  loading.value = false
}

watch(selectedId, loadChart)  // 换设备就重新画

onMounted(async () => {
  chart = echarts.init(document.getElementById('trend-chart'))
  await loadEquipment()
})
</script>

<template>
  <div>
    <div class="header">
      <h2>数据监测</h2>
      <div class="controls">
        <el-input-number v-model="startCycle" placeholder="起始循环" :min="1" style="width: 130px" />
        <span class="sep">至</span>
        <el-input-number v-model="endCycle" placeholder="结束循环" :min="1" style="width: 130px" />
        <el-button @click="loadChart">查询</el-button>
        <el-select v-model="selectedId" placeholder="选择设备" style="width: 160px">
          <el-option v-for="e in equipmentList" :key="e.id" :label="e.code" :value="e.id" />
        </el-select>
      </div>
    </div>
    <div id="trend-chart" v-loading="loading" style="width: 100%; height: 65vh"></div>
    <p class="tip">红点为异常点（3σ 规则：与该设备自身健康时期的基线相比偏离超过 3 倍标准差）</p>
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
.controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sep {
  color: #909399;
}
.tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
