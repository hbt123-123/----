<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">比赛模板</div>
        <div class="actions">
          <el-button type="primary" :icon="Plus" @click="openCreate">新建模板</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <div v-loading="loading">
        <el-empty v-if="!loading && !templates.length" description="还没有模板">
          <el-button type="primary" :icon="Plus" @click="openCreate">新建模板</el-button>
        </el-empty>

        <el-row :gutter="16">
          <el-col
            v-for="t in templates"
            :key="t.id"
            :xs="24"
            :md="12"
            class="tpl-col"
          >
            <el-card shadow="hover" class="tpl-card">
              <template #header>
                <div class="tpl-head">
                  <span class="tpl-name">{{ t.name }}</span>
                  <div class="tpl-tags">
                    <el-tag size="small" type="info">{{ t.stages.length }} 个阶段</el-tag>
                    <el-tag v-if="hasDefense(t)" size="small" type="warning">含答辩</el-tag>
                    <el-tag v-else size="small" type="success">无答辩</el-tag>
                  </div>
                </div>
              </template>

              <el-timeline class="stage-line">
                <el-timeline-item
                  v-for="(s, i) in t.stages"
                  :key="i"
                  :timestamp="s.due_date ? '截止 ' + fmtDue(s.due_date) : '未设截止'"
                  placement="top"
                  :type="s.need_defense ? 'warning' : 'primary'"
                  :hollow="!s.need_defense"
                >
                  <div class="stage-name">
                    <span class="stage-no">{{ s.order }}</span>
                    <span>{{ s.name }}</span>
                    <el-tag v-if="s.need_defense" size="small" type="warning" effect="plain">答辩</el-tag>
                  </div>
                  <div v-if="s.materials.length" class="materials">
                    <el-tag
                      v-for="m in s.materials"
                      :key="m"
                      size="small"
                      effect="plain"
                    >{{ m }}</el-tag>
                  </div>
                  <div v-else class="no-mat">无材料清单</div>
                </el-timeline-item>
              </el-timeline>

              <div class="card-actions">
                <el-button v-if="auth.isAdmin" link type="primary" :icon="Edit" @click="openEdit(t)">编辑</el-button>
                <el-button v-if="auth.isAdmin" link type="primary" :icon="CopyDocument" @click="onClone(t)">复制</el-button>
                <el-button v-if="auth.isAdmin" link type="danger" :icon="Delete" @click="onDelete(t)">删除</el-button>
                <span v-if="!auth.isAdmin" class="readonly-hint">仅部长可编辑</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑模板' : '新建模板'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="dialog.form" label-position="top">
        <el-form-item label="模板名称" required>
          <el-input v-model="dialog.form.name" placeholder="如:大创项目、挑战杯" />
        </el-form-item>
        <div class="stages-head">
          <span class="stages-title">阶段清单</span>
          <el-button size="small" :icon="Plus" @click="addStage">添加阶段</el-button>
        </div>
        <div v-for="(s, i) in dialog.form.stages" :key="i" class="stage-block">
          <div class="stage-row">
            <span class="stage-no">{{ i + 1 }}</span>
            <el-input v-model="s.name" placeholder="阶段名称(如:申报阶段)" class="stage-name-input" />
            <el-date-picker
              v-model="s.due_date"
              type="datetime"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DD HH:mm"
              placeholder="截止时间"
              class="due-input"
            />
            <el-switch v-model="s.need_defense" inline-prompt active-text="答辩" class="defense-switch" />
            <el-button link type="danger" :icon="Delete" @click="removeStage(i)" />
          </div>
          <el-select
            v-model="s.materials"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            placeholder="材料清单(输入后回车添加,可多选)"
            class="mat-select"
          >
            <el-option v-for="m in s.materials" :key="m" :label="m" :value="m" />
          </el-select>
        </div>
        <el-empty v-if="!dialog.form.stages.length" description="还没有阶段,点击上方「添加阶段」" :image-size="50" />
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
import { Plus, Refresh, Edit, Delete, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as templatesApi from '@/api/templates'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const templates = ref([])
const loading = ref(false)

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false,
  tid: '',
  form: { name: '', stages: [] },
})

function emptyStage() {
  return { name: '', due_date: '', need_defense: false, materials: [] }
}

function hasDefense(t) {
  return (t.stages || []).some((s) => s.need_defense)
}

// "2026-10-31 23:59" → "10月31日 23:59"
function fmtDue(d) {
  if (!d) return ''
  const m = String(d).match(/^(\d{4})-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{2})/)
  if (!m) return d
  return `${parseInt(m[2], 10)}月${parseInt(m[3], 10)}日 ${m[4]}:${m[5]}`
}

async function load() {
  loading.value = true
  try {
    templates.value = await templatesApi.listTemplates()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialog.isEdit = false
  dialog.tid = ''
  dialog.form = { name: '', stages: [emptyStage()] }
  dialog.visible = true
}

function openEdit(t) {
  dialog.isEdit = true
  dialog.tid = t.id
  dialog.form = {
    name: t.name,
    stages: (t.stages || []).map((s) => ({
      name: s.name,
      due_date: s.due_date || '',
      need_defense: !!s.need_defense,
      materials: [...(s.materials || [])],
    })),
  }
  dialog.visible = true
}

function addStage() {
  dialog.form.stages.push(emptyStage())
}

function removeStage(i) {
  dialog.form.stages.splice(i, 1)
}

async function onSave() {
  if (!dialog.form.name.trim()) return ElMessage.warning('请输入模板名称')
  const stages = dialog.form.stages.filter((s) => s.name.trim())
  if (!stages.length) return ElMessage.warning('至少添加一个阶段')
  const payload = {
    name: dialog.form.name.trim(),
    stages: stages.map((s) => ({
      name: s.name.trim(),
      due_date: s.due_date || '',
      need_defense: !!s.need_defense,
      materials: s.materials.map((m) => String(m).trim()).filter(Boolean),
    })),
  }
  dialog.saving = true
  try {
    if (dialog.isEdit) {
      await templatesApi.updateTemplate(dialog.tid, payload)
      ElMessage.success('模板已更新')
    } else {
      await templatesApi.createTemplate(payload)
      ElMessage.success('模板已创建')
    }
    dialog.visible = false
    await load()
  } finally {
    dialog.saving = false
  }
}

async function onClone(t) {
  await templatesApi.cloneTemplate(t.id)
  ElMessage.success(`已复制「${t.name}」为「${t.name} 副本」`)
  await load()
}

async function onDelete(t) {
  await ElMessageBox.confirm(
    `确认删除模板「${t.name}」?该操作不可恢复。`,
    '提示',
    { type: 'warning' }
  )
  await templatesApi.deleteTemplate(t.id)
  ElMessage.success('已删除')
  await load()
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
.tpl-col {
  margin-bottom: 16px;
}
.tpl-card {
  height: 100%;
}
.tpl-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tpl-name {
  font-size: 15px;
  font-weight: 600;
}
.tpl-tags {
  display: flex;
  gap: 6px;
}
.stage-line {
  padding: 4px 0 0 4px;
}
.stage-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 6px;
}
.stage-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  font-size: 12px;
}
.materials {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.no-mat {
  color: #909399;
  font-size: 12px;
}
.card-actions {
  display: flex;
  gap: 4px;
  border-top: 1px solid #ebeef5;
  margin-top: 12px;
  padding-top: 10px;
}
.readonly-hint {
  color: #909399;
  font-size: 12px;
}
.stages-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.stages-title {
  font-weight: 600;
  font-size: 14px;
}
.stage-block {
  background: #f7f9fc;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.stage-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.stage-name-input {
  flex: 1;
}
.due-input {
  width: 200px;
}
.defense-switch {
  margin-left: 4px;
}
.mat-select {
  width: 100%;
}
</style>
