<template>
  <el-card shadow="never" class="panel">
    <div class="toolbar">
      <div class="title">答辩评审<span class="sub">安排 · 评委 · 顺序 · 成绩</span></div>
      <div class="actions">
        <el-button v-if="!isOfficer" type="primary" :icon="Plus" @click="openCreate">新建答辩场次</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!loading && !sessions.length" description="还没有答辩场次,可对勾选「需要答辩」的阶段新建场次" :image-size="50">
        <el-button v-if="!isOfficer && defenseStages.length" type="primary" :icon="Plus" @click="openCreate">新建答辩场次</el-button>
        <p v-else-if="!defenseStages.length" class="muted-tip">当前项目没有「需要答辩」的阶段,请在模板或阶段设置中勾选</p>
      </el-empty>

      <div v-for="s in sessions" :key="s.session_id" class="session-card">
        <div class="session-head">
          <div class="head-left">
            <el-tag :type="statusType(s.status)" size="small" effect="dark">{{ s.status }}</el-tag>
            <span class="stage-name">{{ s.stage_name }}</span>
          </div>
          <div class="head-right">
            <el-button v-if="!isOfficer" link type="primary" @click="openEdit(s)">编辑</el-button>
            <el-button v-if="!isOfficer" link type="danger" @click="onDelete(s)">删除</el-button>
          </div>
        </div>
        <div class="session-meta">
          <span class="meta-item"><el-icon><Clock /></el-icon> {{ s.date || '未设置时间' }}</span>
          <span class="meta-item"><el-icon><Location /></el-icon> {{ s.location || '未设置地点' }}</span>
          <span class="meta-item judges">
            <el-icon><User /></el-icon>
            <template v-if="s.judges && s.judges.length">
              <el-tag v-for="(j, i) in s.judges" :key="i" size="small" effect="plain" class="judge-tag">{{ j }}</el-tag>
            </template>
            <span v-else class="muted">未设置评委</span>
          </span>
        </div>

        <el-table :data="s.arrangements" stripe border size="small" class="arr-table">
          <el-table-column label="出场顺序" width="100" align="center">
            <template #default="{ row, $index }">
              <div class="order-cell">
                <span class="order-no">{{ row.order }}</span>
                <div v-if="!isOfficer" class="order-btns">
                  <el-button link size="small" :disabled="$index === 0" @click="moveUp(s, $index)">↑</el-button>
                  <el-button link size="small" :disabled="$index === s.arrangements.length - 1" @click="moveDown(s, $index)">↓</el-button>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="team_name" label="团队" min-width="120" />
          <el-table-column label="答辩成绩" width="130" align="center">
            <template #default="{ row }">
              <el-input-number
                v-if="!isOfficer"
                v-model="row.score"
                :min="0"
                :max="100"
                :precision="1"
                :step="0.5"
                size="small"
                controls-position="right"
                style="width:110px"
                @change="markDirty(s)"
              />
              <span v-else :class="['score-show', { filled: row.score }]">{{ row.score || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="评语" min-width="200">
            <template #default="{ row }">
              <el-input
                v-if="!isOfficer"
                v-model="row.comment"
                size="small"
                placeholder="评语(可选)"
                @input="markDirty(s)"
              />
              <span v-else>{{ row.comment || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="!isOfficer" class="arr-actions">
          <el-button size="small" :icon="Sort" @click="shuffle(s)">随机抽签</el-button>
          <el-button size="small" :icon="Sort" @click="sortByTeam(s)">按团队名排序</el-button>
          <el-button size="small" type="success" :loading="savingId === s.session_id" :disabled="!s._dirty" @click="saveArrangements(s)">保存成绩</el-button>
        </div>
      </div>
    </div>

    <!-- 新建 / 编辑 答辩场次 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑答辩场次' : '新建答辩场次'" width="520px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item v-if="!dialog.isEdit" label="答辩阶段" required>
          <el-select v-model="dialog.form.stage_id" style="width:100%" placeholder="选择需要答辩的阶段">
            <el-option
              v-for="st in availableStages"
              :key="st.stage_id"
              :label="st.name"
              :value="st.stage_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="答辩阶段">
          <el-input :value="dialog.form.stage_name" disabled />
        </el-form-item>
        <el-form-item label="答辩时间">
          <el-input v-model="dialog.form.date" placeholder="如 2026-06-30 14:00" />
        </el-form-item>
        <el-form-item label="答辩地点">
          <el-input v-model="dialog.form.location" placeholder="如 文科楼A301" />
        </el-form-item>
        <el-form-item label="评委">
          <div class="judges-input">
            <el-tag
              v-for="(j, i) in dialog.form.judges"
              :key="i"
              closable
              size="small"
              class="judge-tag"
              @close="dialog.form.judges.splice(i, 1)"
            >{{ j }}</el-tag>
            <el-input
              v-if="judgeInputVisible"
              ref="judgeInputRef"
              v-model="judgeInputValue"
              size="small"
              style="width:120px"
              placeholder="姓名"
              @keyup.enter="addJudge"
              @blur="addJudge"
            />
            <el-button v-else size="small" :icon="Plus" @click="showJudgeInput">添加评委</el-button>
          </div>
        </el-form-item>
        <el-form-item v-if="dialog.isEdit" label="状态">
          <el-radio-group v-model="dialog.form.status">
            <el-radio label="待开始">待开始</el-radio>
            <el-radio label="进行中">进行中</el-radio>
            <el-radio label="已完成">已完成</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSubmit">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { Plus, Refresh, Clock, Location, User, Sort } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as defensesApi from '@/api/defenses'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  pid: { type: String, default: '' },
  stages: { type: Array, default: () => [] },
})

const auth = useAuthStore()
const sessions = ref([])
const loading = ref(false)
const savingId = ref('')
const isOfficer = computed(() => auth.role === '干事')

// 可建答辩的阶段(need_defense=true 且尚未建场)
const defenseStages = computed(() =>
  (props.stages || []).filter((s) => s.need_defense)
)
const availableStages = computed(() => {
  const used = new Set(sessions.value.map((s) => s.stage_id))
  return defenseStages.value.filter((s) => !used.has(s.stage_id))
})

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false,
  sid: '',
  form: { stage_id: '', stage_name: '', date: '', location: '', judges: [], status: '待开始' },
})

const judgeInputVisible = ref(false)
const judgeInputValue = ref('')
const judgeInputRef = ref(null)

function statusType(s) {
  return s === '已完成' ? 'success' : s === '进行中' ? 'warning' : 'info'
}

function markDirty(s) {
  s._dirty = true
}

async function load() {
  if (!props.pid) return
  loading.value = true
  try {
    const list = await defensesApi.listDefenses(props.pid)
    sessions.value = (list || []).map((s) => ({ ...s, _dirty: false }))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  if (!availableStages.value.length) {
    ElMessage.warning('没有可建答辩的阶段(所有需答辩阶段已建场)')
    return
  }
  dialog.isEdit = false
  dialog.sid = ''
  dialog.form = { stage_id: '', stage_name: '', date: '', location: '', judges: [], status: '待开始' }
  dialog.visible = true
}

function openEdit(s) {
  dialog.isEdit = true
  dialog.sid = s.session_id
  dialog.form = {
    stage_id: s.stage_id,
    stage_name: s.stage_name,
    date: s.date || '',
    location: s.location || '',
    judges: [...(s.judges || [])],
    status: s.status || '待开始',
  }
  dialog.visible = true
}

function showJudgeInput() {
  judgeInputVisible.value = true
  judgeInputValue.value = ''
  nextTick(() => judgeInputRef.value?.focus?.())
}

function addJudge() {
  const v = judgeInputValue.value.trim()
  if (v && !dialog.form.judges.includes(v)) {
    dialog.form.judges.push(v)
  }
  judgeInputVisible.value = false
  judgeInputValue.value = ''
}

async function onSubmit() {
  if (!dialog.isEdit && !dialog.form.stage_id) {
    return ElMessage.warning('请选择答辩阶段')
  }
  dialog.saving = true
  try {
    const payload = {
      date: dialog.form.date,
      location: dialog.form.location,
      judges: dialog.form.judges,
    }
    if (dialog.isEdit) {
      payload.status = dialog.form.status
      const updated = await defensesApi.updateDefense(props.pid, dialog.sid, payload)
      const idx = sessions.value.findIndex((s) => s.session_id === dialog.sid)
      if (idx >= 0) sessions.value[idx] = { ...updated, _dirty: false }
      ElMessage.success('已更新答辩场次')
    } else {
      payload.stage_id = dialog.form.stage_id
      const created = await defensesApi.createDefense(props.pid, payload)
      sessions.value.push({ ...created, _dirty: false })
      ElMessage.success('已创建答辩场次')
    }
    dialog.visible = false
  } finally {
    dialog.saving = false
  }
}

async function onDelete(s) {
  try {
    await ElMessageBox.confirm(`确认删除「${s.stage_name}」答辩场次?成绩将一并删除`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  await defensesApi.deleteDefense(props.pid, s.session_id)
  sessions.value = sessions.value.filter((x) => x.session_id !== s.session_id)
  ElMessage.success('已删除')
}

function moveUp(s, idx) {
  if (idx === 0) return
  const arr = s.arrangements
  ;[arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]]
  arr.forEach((a, i) => (a.order = i + 1))
  markDirty(s)
}

function moveDown(s, idx) {
  const arr = s.arrangements
  if (idx === arr.length - 1) return
  ;[arr[idx + 1], arr[idx]] = [arr[idx], arr[idx + 1]]
  arr.forEach((a, i) => (a.order = i + 1))
  markDirty(s)
}

function shuffle(s) {
  const arr = [...s.arrangements]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  arr.forEach((a, i) => (a.order = i + 1))
  s.arrangements = arr
  markDirty(s)
}

function sortByTeam(s) {
  const arr = [...s.arrangements].sort((a, b) =>
    String(a.team_name).localeCompare(String(b.team_name), 'zh')
  )
  arr.forEach((a, i) => (a.order = i + 1))
  s.arrangements = arr
  markDirty(s)
}

async function saveArrangements(s) {
  savingId.value = s.session_id
  try {
    const updated = await defensesApi.updateDefense(props.pid, s.session_id, {
      arrangements: s.arrangements,
    })
    const idx = sessions.value.findIndex((x) => x.session_id === s.session_id)
    if (idx >= 0) sessions.value[idx] = { ...updated, _dirty: false }
    ElMessage.success('已保存出场顺序与成绩')
  } finally {
    savingId.value = ''
  }
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
  color: #0c0d0e;
}
.sub {
  font-size: 12px;
  font-weight: normal;
  color: #a0a2a7;
  margin-left: 4px;
}
.actions {
  display: flex;
  gap: 8px;
}
.muted-tip {
  color: #a0a2a7;
  font-size: 12px;
  margin: 8px 0 0;
}
.session-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: #fafbfc;
}
.session-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stage-name {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.session-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #4a5056;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.meta-item.judges {
  flex-wrap: wrap;
}
.judge-tag {
  margin-right: 4px;
}
.muted {
  color: #c7ccd6;
}
.arr-table {
  margin-top: 4px;
}
.order-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.order-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ebf1ff;
  color: #1664ff;
  font-size: 12px;
  font-weight: 600;
}
.order-btns {
  display: flex;
  flex-direction: column;
  line-height: 1;
}
.order-btns :deep(.el-button) {
  padding: 0;
  height: 14px;
  font-size: 12px;
}
.score-show {
  color: #c7ccd6;
}
.score-show.filled {
  color: #1664ff;
  font-weight: 600;
}
.arr-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.judges-input {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
