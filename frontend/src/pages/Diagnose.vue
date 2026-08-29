<script setup>
// 智能诊断页：对一条预警运行规则引擎，展示疑似故障、分层排查步骤、维修措施
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const alarmList = ref([])       // 未处理的预警（下拉选择）
const selectedAlarm = ref(null)
const loading = ref(false)
const result = ref(null)        // 诊断结果

async function loadAlarms() {
  const resp = await api.get('/alarms', { params: { status: '未处理' } })
  alarmList.value = resp.data
}

async function runDiagnose() {
  if (selectedAlarm.value === null) {
    ElMessage.warning('先选一条预警')
    return
  }
  loading.value = true
  const resp = await api.post(`/diagnose/${selectedAlarm.value}`)
  result.value = resp.data
  loading.value = false
}

onMounted(async () => {
  await loadAlarms()
  // 如果是从预警中心跳过来的，自动选中那条预警并直接诊断
  if (route.query.alarm_id) {
    selectedAlarm.value = Number(route.query.alarm_id)
    runDiagnose()
  }
})
</script>

<template>
  <div>
    <div class="header">
      <h2>智能诊断</h2>
      <div>
        <el-select v-model="selectedAlarm" placeholder="选择预警（未处理）" style="width: 320px; margin-right: 12px">
          <el-option v-for="a in alarmList" :key="a.id" :value="a.id"
                     :label="`#${a.id} ${a.alarm_type}（${a.level}）${a.message}`" />
        </el-select>
        <el-button type="primary" :loading="loading" @click="runDiagnose">开始诊断</el-button>
      </div>
    </div>

    <template v-if="result">
      <el-alert type="info" :closable="false" class="summary">
        异常传感器：{{ result.abnormal_sensors.join('、') || '无' }}　｜　
        当前剩余寿命：{{ result.rul.toFixed(1) }} 循环　｜　
        命中规则 {{ result.matched_count }} 条
      </el-alert>

      <!-- 每条命中的规则一张卡片 -->
      <el-card v-for="m in result.matched" :key="m.rule_id" class="rule-card">
        <template #header>
          <b>[{{ m.rule_id }}] {{ m.fault }}</b>
        </template>
        <p><b>分层排查步骤：</b></p>
        <p v-for="s in m.steps" :key="s" class="step">{{ s }}</p>
        <p><b>维修措施：</b>{{ m.action }}</p>
      </el-card>
    </template>
    <el-empty v-else description="选择一条预警后点击「开始诊断」" />
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
.summary {
  margin-bottom: 16px;
}
.rule-card {
  margin-bottom: 12px;
}
.step {
  margin: 4px 0 4px 16px;
  color: #606266;
}
</style>
