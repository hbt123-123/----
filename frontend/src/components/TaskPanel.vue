<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">材料任务</div>
      <div class="actions">
        <el-select v-model="filterStage" placeholder="按阶段筛选" clearable size="small" style="width:160px" @change="load">
          <el-option v-for="s in stages" :key="s.stage_id" :label="s.name" :value="s.stage_id" />
        </el-select>
        <el-button v-if="!isOfficer" type="primary" :icon="Plus" @click="openGenerate">批量生成任务</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-table :data="tasks" v-loading="loading" stripe border size="small">
      <el-table-column prop="team_name" label="团队" min-width="100" />
      <el-table-column prop="material" label="材料" min-width="120" />
      <el-table-column prop="stage_name" label="阶段" width="100" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="负责干事" width="90">
        <template #default="{ row }">{{ userName(row.assignee_id) || '—' }}</template>
      </el-table-column>
      <el-table-column label="截止" width="100">
        <template #default="{ row }">{{ fmtDue(row.due_date) }}</template>
      </el-table-column>
      <el-table-column label="文件" min-width="130">
        <template #default="{ row }">
          <span v-if="row.file_name" class="file-cell">
            <el-link type="primary" @click="download(row)">{{ row.file_name }}</el-link>
            <el-tag v-if="row.file_versions && row.file_versions.length" size="small" type="info" effect="plain">v{{ row.file_versions.length + 1 }}</el-tag>
          </span>
          <span v-else class="muted">未交</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="210" fixed="right">
        <template #default="{ row }">
          <el-upload
            :show-file-list="false"
            :before-upload="(f) => onUpload(row, f)"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.7z,.jpg,.jpeg,.png"
          >
            <el-button link type="primary" :icon="Upload">上传</el-button>
          </el-upload>
          <el-button v-if="!isOfficer && row.status === '已提交'" link type="success" @click="openReview(row, 'pass')">通过</el-button>
          <el-button v-if="!isOfficer && row.status === '已提交'" link type="warning" @click="openReview(row, 'reject')">打回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && !tasks.length" description="还没有任务,点击「批量生成任务」" :image-size="50" />

    <!-- 批量生成 -->
    <el-dialog v-model="gen.visible" title="批量生成任务" width="560px">
      <el-form :model="gen.form" label-width="90px">
        <el-form-item label="阶段" required>
          <el-select v-model="gen.form.stage_id" style="width:100%" @change="onStageChange">
            <el-option v-for="s in stages" :key="s.stage_id" :label="s.name" :value="s.stage_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="团队" required>
          <el-select v-model="gen.form.team_ids" multiple filterable style="width:100%" placeholder="选择团队(可多选)">
            <el-option v-for="t in teams" :key="t.team_id" :label="t.name" :value="t.team_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="材料清单" required>
          <el-select v-model="gen.form.materials" multiple style="width:100%" placeholder="选择材料项">
            <el-option v-for="m in gen.materials" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="指派干事">
          <el-select v-model="gen.form.assignee_id" clearable filterable style="width:100%" placeholder="可选,指派负责干事">
            <el-option v-for="o in officers" :key="o.id" :label="o.name" :value="o.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="gen.visible = false">取消</el-button>
        <el-button type="primary" :loading="gen.saving" @click="onGenerate">生成</el-button>
      </template>
    </el-dialog>

    <!-- 审核 -->
    <el-dialog v-model="review.visible" :title="review.action === 'pass' ? '审核通过' : '打回原因'" width="440px">
      <el-input v-model="review.comment" type="textarea" :rows="3" :placeholder="review.action === 'pass' ? '备注(可选)' : '请填写打回原因'" />
      <template #footer>
        <el-button @click="review.visible = false">取消</el-button>
        <el-button type="primary" :loading="review.saving" @click="onReview">确认</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Plus, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as tasksApi from '@/api/tasks'
import * as teamsApi from '@/api/teams'
import * as usersApi from '@/api/users'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  pid: { type: String, default: '' },
  stages: { type: Array, default: () => [] },
})

const auth = useAuthStore()
const tasks = ref([])
const teams = ref([])
const users = ref([])
const loading = ref(false)
const filterStage = ref('')

const isOfficer = computed(() => auth.role === '干事')
const officers = computed(() => users.value.filter((u) => u.role === '干事'))

const gen = reactive({ visible: false, saving: false, form: { stage_id: '', team_ids: [], materials: [], assignee_id: '' }, materials: [] })
const review = reactive({ visible: false, saving: false, action: 'pass', comment: '', tid: '' })

function statusType(s) {
  return s === '已通过' ? 'success' : s === '已提交' ? 'primary' : s === '已打回' ? 'danger' : 'info'
}
function userName(id) {
  return users.value.find((u) => u.id === id)?.name
}
function fmtDue(d) {
  if (!d) return '—'
  const m = String(d).match(/(\d{4})-(\d{2})-(\d{2})/)
  return m ? `${m[2]}-${m[3]}` : d
}
function download(row) {
  window.open(`/api/projects/${props.pid}/tasks/${row.task_id}/file`)
}

async function load() {
  if (!props.pid) return
  loading.value = true
  try {
    const params = {}
    if (filterStage.value) params.stage_id = filterStage.value
    tasks.value = await tasksApi.listTasks(props.pid, params)
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  if (!props.pid) return
  const [ts, us] = await Promise.all([teamsApi.listTeams(props.pid), usersApi.listUsers()])
  teams.value = ts
  users.value = us
}

function openGenerate() {
  gen.form = { stage_id: '', team_ids: [], materials: [], assignee_id: '' }
  gen.materials = []
  gen.visible = true
}
function onStageChange(sid) {
  const s = props.stages.find((x) => x.stage_id === sid)
  gen.materials = s?.materials || []
  gen.form.materials = []
}
async function onGenerate() {
  if (!gen.form.stage_id || !gen.form.team_ids.length || !gen.form.materials.length)
    return ElMessage.warning('阶段、团队、材料均必选')
  gen.saving = true
  try {
    const res = await tasksApi.generateTasks(props.pid, gen.form)
    ElMessage.success(`已生成 ${res.created} 个任务(共 ${res.total} 个)`)
    gen.visible = false
    await load()
  } finally {
    gen.saving = false
  }
}

async function onUpload(row, file) {
  try {
    await tasksApi.uploadTask(props.pid, row.task_id, file)
    ElMessage.success('上传成功')
    await load()
  } catch (e) {
    // 已提示
  }
  return false
}

function openReview(row, action) {
  review.tid = row.task_id
  review.action = action
  review.comment = ''
  review.visible = true
}
async function onReview() {
  review.saving = true
  try {
    await tasksApi.reviewTask(props.pid, review.tid, { action: review.action, comment: review.comment })
    ElMessage.success(review.action === 'pass' ? '已通过' : '已打回')
    review.visible = false
    await load()
  } finally {
    review.saving = false
  }
}

watch(() => props.pid, () => { load(); loadMeta() })
onMounted(() => { load(); loadMeta() })
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
.muted {
  color: #c7ccd6;
}
.file-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
