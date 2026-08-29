<script setup>
// 健康评估页：选设备 -> 点"开始评估" -> 展示剩余寿命和健康度 -> 历史评估记录
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const equipmentList = ref([])
const selectedId = ref(null)
const loading = ref(false)      // 评估按钮的加载状态
const result = ref(null)        // 本次评估结果
const history = ref([])         // 历史评估记录

async function loadEquipment() {
  const resp = await api.get('/equipment')
  equipmentList.value = resp.data
}

// 选中设备变化时，清空结果并加载它的历史评估记录
async function onSelectChange() {
  result.value = null
  loadHistory()
}

// 只加载历史记录（不清本次结果，评估完刷新列表用）
async function loadHistory() {
  if (selectedId.value !== null) {
    const resp = await api.get(`/predict/history/${selectedId.value}`)
    history.value = resp.data
  }
}

async function runPredict() {
  if (selectedId.value === null) {
    ElMessage.warning('先选一台设备')
    return
  }
  loading.value = true
  const resp = await api.post(`/predict/${selectedId.value}`)
  result.value = resp.data
  loading.value = false
  // 如果触发了预警，提醒用户去预警中心看
  if (resp.data.rul <= 90) {
    ElMessage.warning('剩余寿命偏低，已自动生成预警，请到预警中心查看')
  }
  loadHistory()  // 刷新历史记录（不动本次结果卡片）
}

async function removeHistory(row) {
  await api.delete(`/predict/history/${row.id}`)
  ElMessage.success('记录已删除')
  loadHistory()
}

// 健康度颜色：高分绿、中分橙、低分红
function scoreColor(score) {
  if (score > 60) return '#67c23a'
  if (score > 30) return '#e6a23c'
  return '#f56c6c'
}

onMounted(loadEquipment)
</script>

<template>
  <div>
    <div class="header">
      <h2>健康评估</h2>
      <div>
        <el-select v-model="selectedId" placeholder="选择设备" style="width: 200px; margin-right: 12px"
                   @change="onSelectChange">
          <el-option v-for="e in equipmentList" :key="e.id" :label="e.code" :value="e.id" />
        </el-select>
        <el-button type="primary" :loading="loading" @click="runPredict">开始评估</el-button>
      </div>
    </div>

    <!-- 评估结果卡片 -->
    <div v-if="result" class="cards">
      <el-card class="card">
        <div class="num">{{ result.rul }}</div>
        <div class="label">剩余寿命（循环数）</div>
      </el-card>
      <el-card class="card">
        <div class="num" :style="{ color: scoreColor(result.health_score) }">{{ result.health_score }}</div>
        <div class="label">健康度评分（满分100）</div>
      </el-card>
      <el-card class="card">
        <div class="num small">{{ result.method === 'random_forest' ? '随机森林' : result.method }}</div>
        <div class="label">评估模型</div>
      </el-card>
    </div>
    <el-empty v-else description="选择设备后点击「开始评估」" />

    <!-- 历史评估记录 -->
    <h3 v-if="history.length > 0">历史评估记录</h3>
    <el-table v-if="history.length > 0" :data="history" stripe>
      <el-table-column prop="created_at" label="评估时间" width="180" />
      <el-table-column prop="rul" label="剩余寿命（循环）" width="150" />
      <el-table-column label="健康度" width="120">
        <template #default="{ row }">
          <span :style="{ color: scoreColor(row.health_score), fontWeight: 'bold' }">{{ row.health_score }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="method" label="模型" />
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="removeHistory(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
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
  margin-bottom: 24px;
}
.card {
  flex: 1;
  text-align: center;
}
.num {
  font-size: 40px;
  font-weight: bold;
}
.num.small {
  font-size: 24px;
  line-height: 56px;
}
.label {
  color: #909399;
  margin-top: 8px;
}
</style>
