<template>
  <div v-loading="loading">
    <div class="back-bar">
      <el-button link :icon="ArrowLeft" @click="router.push('/projects')">返回项目列表</el-button>
    </div>

    <el-card v-if="project" shadow="never" class="info-card">
      <div class="proj-head">
        <span class="proj-name">{{ project.name }}</span>
        <el-tag :type="project.status === '进行中' ? 'success' : 'info'" size="small" class="status-tag">{{ project.status }}</el-tag>
      </div>
      <el-descriptions :column="3" border size="small" class="info-desc">
        <el-descriptions-item label="使用模板">{{ project.template_name }}</el-descriptions-item>
        <el-descriptions-item label="年份">{{ project.year }}</el-descriptions-item>
        <el-descriptions-item label="级别">{{ project.level || '—' }}</el-descriptions-item>
        <el-descriptions-item label="负责副部长">
          <span v-if="ownerNames.length">
            <el-tag v-for="n in ownerNames" :key="n" size="small" effect="plain" class="owner-tag">{{ n }}</el-tag>
          </span>
          <span v-else class="muted">未指派</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmtDate(project.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="项目目录">{{ project.dir }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card v-if="stages.length" shadow="never" class="stages-card">
      <div class="section-title">阶段清单</div>
      <el-timeline class="stage-line">
        <el-timeline-item
          v-for="(s, i) in stages"
          :key="i"
          :type="stageType(s.status)"
          :timestamp="fmtRange(s.start_date, s.due_date)"
          placement="top"
        >
          <div class="stage-head">
            <span class="stage-no">{{ s.order }}</span>
            <span class="stage-name">{{ s.name }}</span>
            <el-tag :type="stageType(s.status)" size="small">{{ s.status }}</el-tag>
            <el-tag v-if="s.need_defense" size="small" type="warning" effect="plain">答辩</el-tag>
          </div>
          <div v-if="s.materials && s.materials.length" class="materials">
            <el-tag v-for="m in s.materials" :key="m" size="small" effect="plain">{{ m }}</el-tag>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <TeamPanel v-if="project" :pid="project.id" />

    <FilePanel v-if="project" :pid="project.id" />

    <TaskPanel v-if="project" :pid="project.id" :stages="stages" />

    <ExportPanel v-if="project" :pid="project.id" />

    <WorksheetPanel v-if="project" :pid="project.id" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as projectsApi from '@/api/projects'
import * as usersApi from '@/api/users'
import TeamPanel from '@/components/TeamPanel.vue'
import FilePanel from '@/components/FilePanel.vue'
import TaskPanel from '@/components/TaskPanel.vue'
import ExportPanel from '@/components/ExportPanel.vue'
import WorksheetPanel from '@/components/WorksheetPanel.vue'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const stages = ref([])
const users = ref([])
const loading = ref(false)

const ownerNames = computed(() =>
  (project.value?.owner_ids || [])
    .map((id) => users.value.find((u) => u.id === id)?.name)
    .filter(Boolean)
)

function fmtDate(s) {
  return s ? String(s).slice(0, 10) : '—'
}

function fmtDue(d) {
  const m = String(d).match(/^(\d{4})-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{2})/)
  if (!m) return d
  return `${parseInt(m[2], 10)}月${parseInt(m[3], 10)}日 ${m[4]}:${m[5]}`
}

function fmtRange(a, b) {
  const parts = []
  if (a) parts.push('起 ' + fmtDue(a))
  if (b) parts.push('止 ' + fmtDue(b))
  return parts.length ? parts.join('  ·  ') : '未设时间'
}

function stageType(status) {
  return status === '已完成' ? 'success' : status === '进行中' ? 'primary' : 'info'
}

async function load() {
  loading.value = true
  try {
    const [res, us] = await Promise.all([
      projectsApi.getProject(route.params.id),
      usersApi.listUsers(),
    ])
    project.value = res.project
    stages.value = res.stages || []
    users.value = us
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.back-bar {
  margin-bottom: 12px;
}
.info-card {
  margin-bottom: 16px;
}
.proj-head {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.proj-name {
  font-size: 18px;
  font-weight: 600;
}
.status-tag {
  margin-left: 10px;
}
.info-desc {
  margin-top: 8px;
}
.stages-card {
  margin-bottom: 16px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
}
.stage-line {
  padding: 4px 0 0 4px;
}
.stage-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
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
.stage-name {
  font-weight: 500;
}
.materials {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.owner-tag {
  margin-right: 4px;
}
.muted {
  color: #909399;
}
.placeholder-card {
  margin-bottom: 16px;
}
</style>
