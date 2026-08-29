<script setup>
// 预警中心页：预警列表 + 标记已处理 + 跳转智能诊断
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const list = ref([])
const codeMap = ref({})  // 设备 id -> 编号（ENG-xxx），显示用

async function loadData() {
  const [alarms, equips] = await Promise.all([
    api.get('/alarms'),
    api.get('/equipment'),
  ])
  list.value = alarms.data
  codeMap.value = Object.fromEntries(equips.data.map(e => [e.id, e.code]))
}

async function resolve(row) {
  await api.put(`/alarms/${row.id}/resolve`)
  ElMessage.success('已标记为已处理')
  loadData()
}

function goDiagnose(row) {
  // 带着预警 id 跳到智能诊断页
  router.push({ path: '/diagnose', query: { alarm_id: row.id } })
}

// 级别颜色：严重红、警告橙、提示蓝
function levelType(level) {
  return { 严重: 'danger', 警告: 'warning', 提示: 'primary' }[level] || 'info'
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="header">
      <h2>预警中心</h2>
      <el-button @click="loadData">刷新</el-button>
    </div>

    <el-table :data="list" stripe height="70vh">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="设备" width="110">
        <template #default="{ row }">{{ codeMap[row.equipment_id] || row.equipment_id }}</template>
      </el-table-column>
      <el-table-column prop="alarm_type" label="类型" width="130" />
      <el-table-column label="级别" width="90">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" label="内容" />
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '未处理' ? 'danger' : 'success'" effect="plain">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="goDiagnose(row)">智能诊断</el-button>
          <el-button v-if="row.status === '未处理'" size="small" @click="resolve(row)">标记处理</el-button>
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
</style>
