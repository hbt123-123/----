<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">汇总工作表<span class="sub">可编辑</span></div>
      <div class="actions">
        <el-input v-model="search" placeholder="搜索筛选" size="small" clearable style="width:150px" :prefix-icon="Search" />
        <el-upload v-if="!isOfficer" :show-file-list="false" :before-upload="onImport" accept=".xlsx,.xls">
          <el-button :icon="Upload" size="small">导入Excel</el-button>
        </el-upload>
        <el-button v-if="!isOfficer" :icon="Plus" size="small" @click="openAddColumn">加列</el-button>
        <el-button v-if="!isOfficer" :icon="Plus" size="small" @click="addRow">加行</el-button>
        <el-button :icon="Download" size="small" :disabled="!worksheet.columns.length" @click="download">下载Excel</el-button>
        <el-button v-if="!isOfficer" type="success" :loading="saving" :disabled="!dirty" size="small" @click="save">保存</el-button>
      </div>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!loading && !worksheet.columns.length" description="还没有工作表,可导入Excel或手动加列加行" :image-size="50">
        <el-upload v-if="!isOfficer" :show-file-list="false" :before-upload="onImport" accept=".xlsx,.xls">
          <el-button type="primary" :icon="Upload">导入Excel</el-button>
        </el-upload>
      </el-empty>

      <el-table v-else :data="filteredRows" stripe border size="small" max-height="520">
        <el-table-column type="index" label="#" width="48" fixed />
        <el-table-column
          v-for="col in worksheet.columns"
          :key="col.name"
          :prop="col.name"
          :label="col.name"
          min-width="150"
        >
          <template #header>
            <div class="col-head">
              <span>{{ col.name }}</span>
              <el-tag v-if="col.type === 'auto_file'" size="small" type="warning" effect="plain">自动</el-tag>
              <el-dropdown v-if="!isOfficer" trigger="click" @command="(cmd) => onColCommand(cmd, col)">
                <el-button link size="small"><el-icon><ArrowDown /></el-icon></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">改名</el-dropdown-item>
                    <el-dropdown-item command="toggleType">{{ col.type === 'auto_file' ? '改为手动' : '改为自动判断' }}</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除列</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <template #default="{ row }">
            <el-input v-if="col.type === 'text' && !isOfficer" v-model="row[col.name]" size="small" @input="markDirty" />
            <span v-else class="auto-val" :class="{ yes: row[col.name] === '是', no: row[col.name] === '否' }">{{ row[col.name] || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="!isOfficer" label="操作" width="70" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" size="small" @click="removeRow($index)">删行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="colDialog.visible" :title="colDialog.isEdit ? '编辑列' : '加列'" width="440px">
      <el-form :model="colDialog.form" label-width="70px">
        <el-form-item label="列名" required>
          <el-input v-model="colDialog.form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="colDialog.form.type">
            <el-radio label="text">手动填写</el-radio>
            <el-radio label="auto_file">自动判断</el-radio>
          </el-radio-group>
          <p v-if="colDialog.form.type === 'auto_file'" class="tip">该列自动为「是/否」:该行团队名在后台有文件=是,否则否。需有含「团队」的列。</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="colDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="onColumnSave">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Upload, Plus, Download, Search, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as wsApi from '@/api/worksheets'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ pid: { type: String, default: '' } })
const auth = useAuthStore()
const worksheet = reactive({ columns: [], rows: [] })
const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)
const search = ref('')
const colDialog = reactive({ visible: false, isEdit: false, oldName: '', form: { name: '', type: 'text' } })

const isOfficer = computed(() => auth.role === '干事')

const filteredRows = computed(() => {
  if (!search.value) return worksheet.rows
  const kw = search.value.toLowerCase()
  return worksheet.rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(kw)))
})

function markDirty() {
  dirty.value = true
}

async function load() {
  if (!props.pid) return
  loading.value = true
  try {
    const ws = await wsApi.getWorksheet(props.pid)
    worksheet.columns = ws.columns || []
    worksheet.rows = ws.rows || []
    dirty.value = false
  } finally {
    loading.value = false
  }
}

async function onImport(file) {
  try {
    const ws = await wsApi.importWorksheet(props.pid, file)
    worksheet.columns = ws.columns || []
    worksheet.rows = ws.rows || []
    dirty.value = false
    ElMessage.success('导入成功')
  } catch (e) {
    // 已提示
  }
  return false
}

function openAddColumn() {
  colDialog.isEdit = false
  colDialog.oldName = ''
  colDialog.form = { name: '', type: 'text' }
  colDialog.visible = true
}

function onColCommand(cmd, col) {
  if (cmd === 'rename') {
    colDialog.isEdit = true
    colDialog.oldName = col.name
    colDialog.form = { name: col.name, type: col.type }
    colDialog.visible = true
  } else if (cmd === 'toggleType') {
    col.type = col.type === 'auto_file' ? 'text' : 'auto_file'
    markDirty()
    save()
  } else if (cmd === 'delete') {
    worksheet.columns = worksheet.columns.filter((c) => c.name !== col.name)
    worksheet.rows.forEach((r) => delete r[col.name])
    markDirty()
    save()
  }
}

async function onColumnSave() {
  if (!colDialog.form.name.trim()) return ElMessage.warning('请输入列名')
  if (colDialog.isEdit) {
    const col = worksheet.columns.find((c) => c.name === colDialog.oldName)
    if (col) {
      const oldName = col.name
      col.name = colDialog.form.name.trim()
      col.type = colDialog.form.type
      if (oldName !== col.name) {
        worksheet.rows.forEach((r) => {
          r[col.name] = r[oldName] || ''
          delete r[oldName]
        })
      }
    }
  } else {
    const newCol = { name: colDialog.form.name.trim(), type: colDialog.form.type }
    worksheet.columns.push(newCol)
    worksheet.rows.forEach((r) => { r[newCol.name] = '' })
  }
  colDialog.visible = false
  markDirty()
  await save()
}

function addRow() {
  const row = {}
  worksheet.columns.forEach((c) => { row[c.name] = '' })
  worksheet.rows.push(row)
  markDirty()
}

function removeRow(idx) {
  worksheet.rows.splice(idx, 1)
  markDirty()
}

async function save() {
  if (!dirty.value) return
  saving.value = true
  try {
    const ws = await wsApi.saveWorksheet(props.pid, { columns: worksheet.columns, rows: worksheet.rows })
    worksheet.columns = ws.columns || []
    worksheet.rows = ws.rows || []
    dirty.value = false
  } finally {
    saving.value = false
  }
}

function download() {
  window.open(wsApi.worksheetDownloadUrl(props.pid))
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
  flex-wrap: wrap;
  gap: 8px;
}
.title {
  font-size: 15px;
  font-weight: 600;
}
.sub {
  font-size: 12px;
  font-weight: normal;
  color: #909399;
  margin-left: 4px;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.col-head {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.auto-val.yes {
  color: #67c23a;
  font-weight: 600;
}
.auto-val.no {
  color: #f56c6c;
  font-weight: 600;
}
.tip {
  color: #909399;
  font-size: 12px;
  margin: 4px 0 0;
}
</style>
