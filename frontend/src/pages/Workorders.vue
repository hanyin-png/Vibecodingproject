<script setup>
// 维修工单页：工单列表 + 状态流转（待处理 -> 维修中 -> 已完成）
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const list = ref([])
const codeMap = ref({})

async function loadData() {
  const [orders, equips] = await Promise.all([
    api.get('/workorders'),
    api.get('/equipment'),
  ])
  list.value = orders.data
  codeMap.value = Object.fromEntries(equips.data.map(e => [e.id, e.code]))
}

// 状态的下一步：待处理 -> 维修中 -> 已完成
const NEXT_STATUS = { 待处理: '维修中', 维修中: '已完成' }

async function advance(row) {
  const next = NEXT_STATUS[row.status]
  await api.put(`/workorders/${row.id}/status`, { status: next })
  ElMessage.success(`已更新为「${next}」`)
  loadData()
}

function statusType(status) {
  return { 待处理: 'danger', 维修中: 'warning', 已完成: 'success' }[status]
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="header">
      <h2>维修工单</h2>
      <el-button @click="loadData">刷新</el-button>
    </div>

    <el-table :data="list" stripe height="70vh">
      <el-table-column prop="id" label="工单号" width="80" />
      <el-table-column label="设备" width="110">
        <template #default="{ row }">{{ codeMap[row.equipment_id] || row.equipment_id }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" width="220" />
      <el-table-column label="诊断建议">
        <template #default="{ row }">
          <el-tooltip :content="row.suggestion" placement="top" :show-after="200" max-width="600px">
            <span class="suggestion">{{ row.suggestion }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="130">
        <template #default="{ row }">
          <el-button v-if="NEXT_STATUS[row.status]" size="small" type="primary" @click="advance(row)">
            转为{{ NEXT_STATUS[row.status] }}
          </el-button>
          <span v-else style="color:#909399">已办结</span>
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
.suggestion {
  display: inline-block;
  max-width: 480px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
</style>
