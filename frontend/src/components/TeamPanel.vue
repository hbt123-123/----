<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">参赛团队</div>
      <div class="actions">
        <el-upload :show-file-list="false" :before-upload="onImport" accept=".xlsx,.xls">
          <el-button :icon="Upload">批量导入</el-button>
        </el-upload>
        <el-button type="primary" :icon="Plus" @click="openCreate">添加团队</el-button>
      </div>
    </div>

    <el-table :data="teams" v-loading="loading" stripe border size="small">
      <el-table-column type="index" label="#" width="45" />
      <el-table-column prop="name" label="团队名称" min-width="120" />
      <el-table-column prop="leader" label="队长" width="80" />
      <el-table-column prop="student_id" label="学号" width="110" />
      <el-table-column prop="contact" label="联系方式" width="110" />
      <el-table-column prop="members" label="成员" min-width="120" show-overflow-tooltip />
      <el-table-column prop="advisor" label="指导老师" width="90" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && !teams.length" description="还没有团队,可手动添加或批量导入" :image-size="50" />

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑团队' : '添加团队'" width="500px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="团队名称" required>
          <el-input v-model="dialog.form.name" placeholder="如:张三团队" />
        </el-form-item>
        <el-form-item label="队长">
          <el-input v-model="dialog.form.leader" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="dialog.form.student_id" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="dialog.form.contact" />
        </el-form-item>
        <el-form-item label="成员">
          <el-input v-model="dialog.form.members" type="textarea" :rows="2" placeholder="多个成员用逗号分隔" />
        </el-form-item>
        <el-form-item label="指导老师">
          <el-input v-model="dialog.form.advisor" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="dialog.form.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as teamsApi from '@/api/teams'

const props = defineProps({ pid: { type: String, default: '' } })
const teams = ref([])
const loading = ref(false)

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false,
  tid: '',
  form: {},
})

function emptyForm() {
  return { name: '', leader: '', student_id: '', contact: '', members: '', advisor: '', remark: '' }
}

async function load() {
  if (!props.pid) return
  loading.value = true
  try {
    teams.value = await teamsApi.listTeams(props.pid)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialog.isEdit = false
  dialog.tid = ''
  dialog.form = emptyForm()
  dialog.visible = true
}

function openEdit(row) {
  dialog.isEdit = true
  dialog.tid = row.team_id
  dialog.form = { name: row.name, leader: row.leader, student_id: row.student_id, contact: row.contact, members: row.members, advisor: row.advisor, remark: row.remark }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.name.trim()) return ElMessage.warning('请输入团队名称')
  dialog.saving = true
  try {
    if (dialog.isEdit) {
      await teamsApi.updateTeam(props.pid, dialog.tid, dialog.form)
      ElMessage.success('已更新')
    } else {
      await teamsApi.createTeam(props.pid, dialog.form)
      ElMessage.success('已添加')
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除团队「${row.name}」?`, '提示', { type: 'warning' })
  await teamsApi.deleteTeam(props.pid, row.team_id)
  ElMessage.success('已删除')
  await load()
}

async function onImport(file) {
  try {
    const res = await teamsApi.importTeams(props.pid, file)
    ElMessage.success(`导入完成:新增 ${res.added} 队,跳过 ${res.skipped} 队`)
    await load()
  } catch (e) {
    // 已提示
  }
  return false
}

watch(() => props.pid, load)
onMounted(load)
</script>

<style scoped>
.panel {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
