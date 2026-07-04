<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">成员管理</div>
        <div class="actions">
          <el-upload
            :show-file-list="false"
            :before-upload="onImport"
            accept=".xlsx,.xls"
          >
            <el-button :icon="Upload">批量导入</el-button>
          </el-upload>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增成员</el-button>
        </div>
      </div>

      <el-table :data="users" v-loading="loading" stripe border>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="student_id" label="学号" min-width="120" />
        <el-table-column prop="role" label="角色" width="90">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact" label="联系方式" min-width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
            <el-tag v-else-if="row.activated" type="success" size="small">已激活</el-tag>
            <el-tag v-else type="warning" size="small">未激活</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="!row.is_admin" link type="warning" @click="onReset(row)">重置密码</el-button>
            <el-button v-if="!row.is_admin" link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑成员' : '新增成员'"
      width="460px"
    >
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="dialog.form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="dialog.form.student_id" placeholder="可选" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="dialog.form.role" style="width: 100%">
            <el-option label="部长" value="部长" />
            <el-option label="副部长" value="副部长" />
            <el-option label="干事" value="干事" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="dialog.form.contact" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as usersApi from '@/api/users'

const users = ref([])
const loading = ref(false)

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false,
  uid: '',
  form: { name: '', student_id: '', role: '干事', contact: '' },
})

function roleType(r) {
  return r === '部长' ? 'danger' : r === '副部长' ? 'warning' : 'info'
}

async function load() {
  loading.value = true
  try {
    users.value = await usersApi.listUsers()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialog.isEdit = false
  dialog.uid = ''
  dialog.form = { name: '', student_id: '', role: '干事', contact: '' }
  dialog.visible = true
}

function openEdit(row) {
  dialog.isEdit = true
  dialog.uid = row.id
  dialog.form = {
    name: row.name,
    student_id: row.student_id,
    role: row.role,
    contact: row.contact,
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.name.trim()) return ElMessage.warning('请输入姓名')
  dialog.saving = true
  try {
    if (dialog.isEdit) {
      await usersApi.updateUser(dialog.uid, dialog.form)
      ElMessage.success('已更新')
    } else {
      await usersApi.createUser(dialog.form)
      ElMessage.success('已新增,该成员首次登录时设置密码')
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(
    `确认删除成员「${row.name}」?该操作不可恢复。`,
    '提示',
    { type: 'warning' }
  )
  await usersApi.deleteUser(row.id)
  ElMessage.success('已删除')
  await load()
}

async function onReset(row) {
  await ElMessageBox.confirm(
    `确认重置「${row.name}」的密码?重置后该成员需重新设置密码。`,
    '提示',
    { type: 'warning' }
  )
  await usersApi.resetPassword(row.id)
  ElMessage.success('密码已重置')
  await load()
}

async function onImport(file) {
  try {
    const res = await usersApi.importUsers(file)
    ElMessage.success(`导入完成:新增 ${res.added} 条,跳过 ${res.skipped} 条`)
    await load()
  } catch (e) {
    // 已提示
  }
  return false // 阻止 el-upload 自动上传
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
