<script setup>
// 设备台账页：设备列表 + 新增/编辑/删除
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const list = ref([])          // 设备列表
const dialogVisible = ref(false)  // 新增/编辑弹窗
const editingId = ref(null)   // 正在编辑的设备 id（null 表示新增）
const form = reactive({ code: '', model: 'Turbofan 涡扇发动机', install_date: '2024-01-01', status: '健康' })

async function loadList() {
  const resp = await api.get('/equipment')
  list.value = resp.data
}

function openAdd() {
  editingId.value = null
  Object.assign(form, { code: '', model: 'Turbofan 涡扇发动机', install_date: '2024-01-01', status: '健康' })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function save() {
  if (editingId.value === null) {
    await api.post('/equipment', form)
    ElMessage.success('添加成功')
  } else {
    await api.put(`/equipment/${editingId.value}`, form)
    ElMessage.success('修改成功')
  }
  dialogVisible.value = false
  loadList()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除设备 ${row.code} 吗？`, '提示', { type: 'warning' })
  await api.delete(`/equipment/${row.id}`)
  ElMessage.success('删除成功')
  loadList()
}

onMounted(loadList)
</script>

<template>
  <div>
    <div class="header">
      <h2>设备台账</h2>
      <el-button type="primary" @click="openAdd">新增设备</el-button>
    </div>

    <el-table :data="list" stripe height="70vh">
      <el-table-column prop="code" label="设备编号" width="120" />
      <el-table-column prop="model" label="型号" />
      <el-table-column prop="install_date" label="投运日期" width="140" />
      <el-table-column label="健康状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status === '健康' ? 'success' : (row.status === '预警' ? 'warning' : 'danger')">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId === null ? '新增设备' : '编辑设备'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="编号"><el-input v-model="form.code" placeholder="如 ENG-101" /></el-form-item>
        <el-form-item label="型号"><el-input v-model="form.model" /></el-form-item>
        <el-form-item label="投运日期"><el-input v-model="form.install_date" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="健康" value="健康" />
            <el-option label="预警" value="预警" />
            <el-option label="故障" value="故障" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
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
