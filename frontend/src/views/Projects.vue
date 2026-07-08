<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">项目管理</div>
        <div class="actions">
          <el-button type="primary" :icon="Plus" @click="openWizard">新建项目</el-button>
          <el-button :icon="Refresh" @click="load">刷新</el-button>
        </div>
      </div>

      <el-table :data="projects" v-loading="loading" stripe border>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="项目名称" min-width="180" />
        <el-table-column prop="template_name" label="模板" width="130" />
        <el-table-column prop="year" label="年份" width="80" />
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.level" size="small">{{ row.level }}</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '进行中' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责副部长" min-width="150">
          <template #default="{ row }">
            <span v-if="ownerNames(row.owner_ids).length">
              <el-tag
                v-for="n in ownerNames(row.owner_ids)"
                :key="n"
                size="small"
                effect="plain"
                class="owner-tag"
              >{{ n }}</el-tag>
            </span>
            <span v-else class="muted">未指派</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="110">
          <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/projects/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !projects.length" description="还没有项目,点击「新建项目」创建" />
    </el-card>

    <el-dialog
      v-model="wizard.visible"
      title="新建项目"
      width="720px"
      :close-on-click-modal="false"
    >
      <el-steps :active="wizard.step" finish-status="success" align-center class="wizard-steps">
        <el-step title="选择模板" />
        <el-step title="基本信息" />
        <el-step title="阶段时间" />
      </el-steps>

      <!-- 步骤1:选模板 -->
      <div v-show="wizard.step === 0" class="step-body">
        <el-radio-group v-model="wizard.form.template_id" class="tpl-radio-group">
          <el-radio v-for="t in templates" :key="t.id" :label="t.id" border class="tpl-radio">
            <div class="tpl-option">
              <span class="tpl-option-name">{{ t.name }}</span>
              <span class="tpl-option-meta">{{ t.stages.length }} 个阶段</span>
            </div>
          </el-radio>
        </el-radio-group>
      </div>

      <!-- 步骤2:基本信息 -->
      <div v-show="wizard.step === 1" class="step-body">
        <el-form :model="wizard.form" label-width="100px">
          <el-form-item label="项目名称" required>
            <el-input v-model="wizard.form.name" placeholder="如:2026年大学生创新创业训练计划" />
          </el-form-item>
          <el-form-item label="年份" required>
            <el-input v-model="wizard.form.year" placeholder="如:2026" />
          </el-form-item>
          <el-form-item label="级别">
            <el-select v-model="wizard.form.level" allow-create filterable placeholder="选择或输入级别" style="width:100%">
              <el-option label="院级" value="院级" />
              <el-option label="校级" value="校级" />
              <el-option label="省级" value="省级" />
              <el-option label="国家级" value="国家级" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责副部长">
            <el-select
              v-model="wizard.form.owner_ids"
              multiple
              filterable
              placeholder="可多选(副部长)"
              style="width:100%"
            >
              <el-option
                v-for="u in viceLeaders"
                :key="u.id"
                :label="u.name + (u.student_id ? ' (' + u.student_id + ')' : '')"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤3:阶段时间 -->
      <div v-show="wizard.step === 2" class="step-body">
        <p class="step-tip">各阶段截止时间已从模板预填,可调整;开始日期可选。</p>
        <div v-for="(s, i) in wizard.form.stages" :key="i" class="stage-row-w">
          <span class="stage-no">{{ i + 1 }}</span>
          <span class="stage-label">{{ s.name }}</span>
          <el-date-picker
            v-model="s.start_date"
            type="datetime"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            placeholder="开始(可选)"
            class="date-input"
          />
          <span class="arrow">→</span>
          <el-date-picker
            v-model="s.due_date"
            type="datetime"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            placeholder="截止时间"
            class="date-input"
          />
          <el-tag v-if="s.need_defense" size="small" type="warning">答辩</el-tag>
        </div>
      </div>

      <template #footer>
        <el-button @click="wizard.visible = false">取消</el-button>
        <el-button v-if="wizard.step > 0" @click="wizard.step--">上一步</el-button>
        <el-button v-if="wizard.step < 2" type="primary" @click="nextStep">下一步</el-button>
        <el-button v-if="wizard.step === 2" type="primary" :loading="wizard.saving" @click="onCreate">创建项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as projectsApi from '@/api/projects'
import * as templatesApi from '@/api/templates'
import * as usersApi from '@/api/users'

const router = useRouter()
const projects = ref([])
const templates = ref([])
const users = ref([])
const loading = ref(false)

const wizard = reactive({
  visible: false,
  step: 0,
  saving: false,
  form: {
    template_id: '',
    name: '',
    year: '2026',
    level: '校级',
    owner_ids: [],
    stages: [],
  },
})

const viceLeaders = computed(() => users.value.filter((u) => u.role === '副部长'))

function ownerNames(ids) {
  return (ids || []).map((id) => users.value.find((u) => u.id === id)?.name).filter(Boolean)
}

function fmtDate(s) {
  if (!s) return ''
  return String(s).slice(0, 10)
}

async function load() {
  loading.value = true
  try {
    const [ps, us] = await Promise.all([projectsApi.listProjects(), usersApi.listUsers()])
    projects.value = ps
    users.value = us
  } finally {
    loading.value = false
  }
}

async function openWizard() {
  wizard.step = 0
  wizard.form = { template_id: '', name: '', year: '2026', level: '校级', owner_ids: [], stages: [] }
  if (!templates.value.length) {
    templates.value = await templatesApi.listTemplates()
  }
  wizard.visible = true
}

async function nextStep() {
  if (wizard.step === 0) {
    if (!wizard.form.template_id) return ElMessage.warning('请选择模板')
    const tpl = await templatesApi.getTemplate(wizard.form.template_id)
    wizard.form.stages = (tpl.stages || []).map((s) => ({
      name: s.name,
      need_defense: s.need_defense,
      start_date: '',
      due_date: s.due_date || '',
    }))
    wizard.step = 1
  } else if (wizard.step === 1) {
    if (!wizard.form.name.trim()) return ElMessage.warning('请输入项目名称')
    if (!wizard.form.year.trim()) return ElMessage.warning('请输入年份')
    wizard.step = 2
  }
}

async function onCreate() {
  wizard.saving = true
  try {
    const payload = {
      name: wizard.form.name.trim(),
      year: wizard.form.year.trim(),
      level: wizard.form.level || '',
      template_id: wizard.form.template_id,
      owner_ids: wizard.form.owner_ids,
      stages: wizard.form.stages.map((s) => ({
        start_date: s.start_date || '',
        due_date: s.due_date || '',
      })),
    }
    await projectsApi.createProject(payload)
    ElMessage.success('项目已创建')
    wizard.visible = false
    await load()
  } finally {
    wizard.saving = false
  }
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
.muted {
  color: #909399;
}
.owner-tag {
  margin-right: 4px;
}
.wizard-steps {
  margin-bottom: 24px;
}
.step-body {
  min-height: 200px;
}
.tpl-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.tpl-radio {
  width: 100%;
  height: auto;
  padding: 10px 14px;
  margin-right: 0;
}
.tpl-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.tpl-option-name {
  font-weight: 600;
}
.tpl-option-meta {
  color: #909399;
  font-size: 12px;
}
.step-tip {
  color: #909399;
  font-size: 13px;
  margin: 0 0 12px;
}
.stage-row-w {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.stage-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  font-size: 12px;
}
.stage-label {
  width: 100px;
  font-weight: 500;
}
.date-input {
  width: 180px;
}
.arrow {
  color: #c0c4cc;
}
</style>
