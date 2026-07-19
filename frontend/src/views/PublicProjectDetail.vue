<template>
  <div v-loading="loading" class="public-detail">
    <div class="back-bar">
      <el-button link :icon="ArrowLeft" @click="router.push('/public/projects')">返回公开项目</el-button>
    </div>

    <template v-if="project">
      <!-- 项目信息卡 -->
      <el-card shadow="never" class="info-card">
        <div class="proj-head">
          <span class="proj-name">{{ project.name }}</span>
          <el-tag :type="project.status === '进行中' ? 'success' : 'info'" size="small">{{ project.status }}</el-tag>
          <el-tag v-if="project.level" size="small" effect="plain">{{ project.level }}</el-tag>
        </div>
        <el-descriptions :column="3" border size="small" class="info-desc">
          <el-descriptions-item label="使用模板">{{ project.template_name }}</el-descriptions-item>
          <el-descriptions-item label="年份">{{ project.year }} 年</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmtDate(project.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="参与团队数">{{ teamCount }} 支</el-descriptions-item>
          <el-descriptions-item label="阶段数">{{ stages.length }}</el-descriptions-item>
          <el-descriptions-item label="整体进度">
            <el-progress
              :percentage="pct(taskStats.passed, taskStats.total)"
              :color="progColor(pct(taskStats.passed, taskStats.total))"
              :stroke-width="8"
              class="prog-inline"
            />
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 统计卡 -->
      <el-row :gutter="12" class="stat-row">
        <el-col :xs="12" :sm="6" v-for="(s, i) in statCards" :key="s.key">
          <div
            class="stat-card"
            :class="'stat-' + s.key"
            v-motion
            :initial="{ opacity: 0, y: 16 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: i * 60 } }"
          >
            <div class="stat-icon"><el-icon><component :is="s.icon" /></el-icon></div>
            <div class="stat-body">
              <div class="stat-num">{{ s.value }}</div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 阶段时间线 + 进度 -->
      <el-card v-if="stages.length" shadow="never" class="stages-card">
        <div class="section-title">阶段进度</div>
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
            <div class="stage-prog">
              <div class="sp-line">
                <span class="sp-label">材料完成</span>
                <span class="sp-text">{{ s.done }} / {{ s.total }}</span>
              </div>
              <el-progress
                :percentage="pct(s.done, s.total)"
                :stroke-width="5"
                :color="progColor(pct(s.done, s.total))"
                :show-text="false"
              />
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 答辩场次(公开信息) -->
      <el-card v-if="defenseSessions.length" shadow="never" class="defense-card">
        <div class="section-title">答辩安排</div>
        <el-table :data="defenseSessions" stripe border>
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="stage_name" label="阶段" min-width="120" />
          <el-table-column label="时间" width="170">
            <template #default="{ row }">
              <span v-if="row.date">{{ row.date }}</span>
              <span v-else class="muted">未定</span>
            </template>
          </el-table-column>
          <el-table-column label="地点" min-width="120">
            <template #default="{ row }">
              <span v-if="row.location">{{ row.location }}</span>
              <span v-else class="muted">未定</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="defenseStatusType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="评委数" width="80" align="center">
            <template #default="{ row }">{{ row.judge_count }}</template>
          </el-table-column>
          <el-table-column label="已答辩" width="100" align="center">
            <template #default="{ row }">{{ row.finished_count }} / {{ row.team_count }}</template>
          </el-table-column>
        </el-table>
        <div class="defense-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>答辩评委姓名与团队成绩为内部信息,登录后可查看。</span>
        </div>
      </el-card>

      <!-- 登录提示 -->
      <el-card shadow="never" class="login-tip-card">
        <div class="login-tip">
          <el-icon class="lt-icon"><Lock /></el-icon>
          <div class="lt-text">
            <div class="lt-title">需要查看完整信息?</div>
            <div class="lt-desc">登录后可查看团队列表、材料提交、答辩成绩等详细数据。</div>
          </div>
          <el-button type="primary" @click="goLogin">前往登录</el-button>
        </div>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="项目不存在或未公开">
      <el-button type="primary" @click="router.push('/public/projects')">返回列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Lock, InfoFilled, Files, CircleCheck, Clock, Warning } from '@element-plus/icons-vue'
import * as publicApi from '@/api/public'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const stages = ref([])
const taskStats = ref({ total: 0, passed: 0, submitted: 0, pending: 0, rejected: 0 })
const teamCount = ref(0)
const defenseSessions = ref([])
const loading = ref(false)

const statCards = computed(() => [
  { key: 'total', label: '材料总数', value: taskStats.value.total, icon: Files },
  { key: 'passed', label: '已通过', value: taskStats.value.passed, icon: CircleCheck },
  { key: 'submitted', label: '待审核', value: taskStats.value.submitted, icon: Clock },
  { key: 'pending', label: '未提交', value: taskStats.value.pending, icon: Warning },
])

function pct(a, b) {
  if (!b) return 0
  return Math.round((a / b) * 100)
}
function progColor(p) {
  if (p >= 100) return '#1ebf6f'
  if (p >= 60) return '#1664ff'
  if (p >= 30) return '#bd7e00'
  return '#f65159'
}
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
function defenseStatusType(s) {
  return { '待开始': 'info', '进行中': 'warning', '已完成': 'success' }[s] || 'info'
}
function goLogin() {
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

async function load() {
  loading.value = true
  try {
    const res = await publicApi.getPublicProject(route.params.id)
    project.value = res.project
    stages.value = res.stages || []
    taskStats.value = res.task_stats || taskStats.value
    teamCount.value = res.team_count || 0
    defenseSessions.value = res.defense_sessions || []
  } catch (e) {
    project.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.public-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.back-bar {
  margin-bottom: -4px;
}
.info-card {
  border-radius: 12px;
}
.proj-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.proj-name {
  font-size: 18px;
  font-weight: 600;
  color: #0c0d0e;
}
.info-desc {
  margin-top: 8px;
}
.prog-inline {
  max-width: 240px;
}

/* 统计卡 */
.stat-row {
  margin-bottom: 0;
}
.stat-card {
  background: #ffffff;
  border: 1px solid #eaedf1;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: transform 0.18s, box-shadow 0.18s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.stat-total .stat-icon { background: #ebf1ff; color: #1664ff; }
.stat-passed .stat-icon { background: #eef9f1; color: #1ebf6f; }
.stat-submitted .stat-icon { background: #fef8eb; color: #bd7e00; }
.stat-pending .stat-icon { background: #fdf5f5; color: #f65159; }
.stat-num {
  font-size: 22px;
  font-weight: 600;
  color: #0c0d0e;
  line-height: 1.1;
}
.stat-label {
  font-size: 12px;
  color: #737a87;
  margin-top: 2px;
}

/* 区块 */
.stages-card,
.defense-card,
.login-tip-card {
  border-radius: 12px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
  margin-bottom: 14px;
}
.stage-line {
  padding: 4px 0 0 4px;
}
.stage-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.stage-no {
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
.stage-name {
  font-weight: 500;
}
.materials {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.stage-prog {
  margin-top: 6px;
  max-width: 420px;
}
.sp-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.sp-label {
  font-size: 12px;
  color: #42464e;
}
.sp-text {
  font-size: 12px;
  color: #737a87;
}
.muted {
  color: #c7ccd6;
}

/* 答辩 */
.defense-tip {
  margin-top: 10px;
  padding: 8px 12px;
  background: #f6f8fa;
  border-radius: 6px;
  font-size: 12px;
  color: #737a87;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 登录提示 */
.login-tip-card {
  background: linear-gradient(135deg, #ebf1ff 0%, #f6faff 100%);
  border-color: #c5dbff;
}
.login-tip {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.lt-icon {
  font-size: 32px;
  color: #1664ff;
  flex-shrink: 0;
}
.lt-text {
  flex: 1;
  min-width: 200px;
}
.lt-title {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.lt-desc {
  font-size: 12px;
  color: #42464e;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 767px) {
  .info-desc :deep(.el-descriptions) {
    --el-descriptions-column: 1 !important;
  }
  .progInline {
    max-width: 100%;
  }
  .stage-prog {
    max-width: 100%;
  }
  .login-tip {
    flex-direction: column;
    text-align: center;
  }
}
</style>
