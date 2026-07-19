<template>
  <div class="dashboard" v-loading="loading">
    <!-- ============ 部长 / 副部长视图 ============ -->
    <template v-if="!isStaff">
      <!-- 顶部统计卡片 -->
      <el-row :gutter="16" class="stat-row">
        <el-col :xs="12" :sm="6" v-for="(s, i) in stats" :key="s.key">
          <el-card
            shadow="never"
            class="stat-card"
            :class="['stat-' + s.key, { clickable: s.scroll }]"
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: i * 80 } }"
            @click="s.scroll && scrollTo(s.scroll)"
          >
            <div class="stat-inner">
              <div class="stat-icon">
                <el-icon><component :is="s.icon" /></el-icon>
              </div>
              <div class="stat-body">
                <div class="stat-num">{{ s.value }}</div>
                <div class="stat-label">{{ s.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 项目进度卡片网格 -->
      <el-card shadow="never" class="section-card">
        <div class="section-title">
          <span>项目进度</span>
          <el-button link type="primary" @click="router.push('/projects')">进入项目</el-button>
        </div>
        <el-empty v-if="!projects.length" description="暂无项目" :image-size="80" />
        <el-row :gutter="16" v-else>
          <el-col :xs="24" :md="12" v-for="(p, i) in projects" :key="p.id">
            <div
              class="proj-card"
              v-motion
              :initial="{ opacity: 0, y: 16 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: i * 60 } }"
              @click="router.push('/projects/' + p.id)"
            >
              <div class="proj-head">
                <div class="proj-title">
                  <span class="proj-name">{{ p.name }}</span>
                  <el-tag size="small" :type="p.status === '进行中' ? 'success' : 'info'">{{ p.status }}</el-tag>
                  <el-tag v-if="p.level" size="small" effect="plain">{{ p.level }}</el-tag>
                </div>
                <div class="proj-meta">
                  <span>{{ p.template_name }}</span>
                  <span class="dot">·</span>
                  <span>{{ p.year }}</span>
                  <template v-if="p.owner_names && p.owner_names.length">
                    <span class="dot">·</span>
                    <span>{{ p.owner_names.join('、') }}</span>
                  </template>
                </div>
              </div>
              <div class="proj-progress">
                <div class="prog-line">
                  <span class="prog-label">整体进度</span>
                  <span class="prog-text">{{ p.task_stats.passed }} / {{ p.task_stats.total }}</span>
                </div>
                <el-progress
                  :percentage="pct(p.task_stats.passed, p.task_stats.total)"
                  :stroke-width="8"
                  :color="progColor(pct(p.task_stats.passed, p.task_stats.total))"
                />
              </div>
              <div class="stage-list">
                <div v-for="st in p.stage_progress" :key="st.stage_id" class="stage-item">
                  <div class="stage-head">
                    <span class="stage-name">
                      {{ st.name }}
                      <el-tag v-if="st.need_defense" size="small" type="warning" effect="plain">答辩</el-tag>
                      <el-tooltip v-if="st.overdue > 0" :content="st.overdue + ' 个逾期任务'" placement="top">
                        <el-tag size="small" type="danger" effect="plain">{{ st.overdue }} 逾期</el-tag>
                      </el-tooltip>
                    </span>
                    <span class="stage-due" :class="{ overdue: isStageOverdue(st) }">{{ st.due_date || '未设截止' }}</span>
                  </div>
                  <el-progress
                    :percentage="pct(st.done, st.total)"
                    :stroke-width="5"
                    :color="progColor(pct(st.done, st.total))"
                  />
                </div>
              </div>
              <div class="proj-stats">
                <span class="ps-item"><b>{{ p.task_stats.total }}</b> 总任务</span>
                <span class="ps-item ps-pass"><b>{{ p.task_stats.passed }}</b> 已通过</span>
                <span class="ps-item ps-sub"><b>{{ p.task_stats.submitted }}</b> 待审核</span>
                <span class="ps-item ps-pend"><b>{{ p.task_stats.pending }}</b> 待办</span>
                <span class="ps-item ps-over" v-if="p.task_stats.overdue"><b>{{ p.task_stats.overdue }}</b> 逾期</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 人员负荷 -->
      <el-card shadow="never" class="section-card">
        <div class="section-title"><span>人员负荷</span></div>
        <el-empty v-if="!workload.length" description="暂无指派任务" :image-size="80" />
        <div v-else class="workload-list">
          <div v-for="w in workload" :key="w.user_id" class="wl-item">
            <div class="wl-info">
              <span class="wl-name">{{ w.name }}</span>
              <el-tag size="small" effect="plain" :type="w.role === '副部长' ? 'primary' : 'info'">{{ w.role }}</el-tag>
            </div>
            <div class="wl-bar-wrap">
              <div class="wl-bar" :style="{ width: wlWidth(w.total) + '%' }">
                <span class="wl-bar-text">{{ w.total }} 任务</span>
              </div>
            </div>
            <div class="wl-stats">
              <span class="wl-stat wl-review">待审 {{ w.pending_review }}</span>
              <span class="wl-stat" :class="{ 'wl-over': w.overdue > 0 }">逾期 {{ w.overdue }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 预警区 -->
      <el-row :gutter="16" class="alert-row" ref="alertRowRef">
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="alert-card alert-overdue">
            <div class="section-title">
              <span class="alert-title-danger">逾期任务</span>
              <div class="title-right">
                <el-tag size="small" type="danger" round>{{ alerts.overdue.length }}</el-tag>
                <el-button
                  v-if="alerts.overdue.length && !isStaff"
                  size="small"
                  type="danger"
                  plain
                  :loading="reminding.overdue"
                  @click="remind('overdue')"
                >全部催办</el-button>
              </div>
            </div>
            <el-empty v-if="!alerts.overdue.length" description="无逾期" :image-size="60" />
            <div v-else class="alert-list">
              <div v-for="a in alerts.overdue.slice(0, 20)" :key="a.task_id" class="alert-item alert-item-danger" @click="router.push('/projects/' + a.project_id)">
                <div class="ai-title">{{ a.project_name }} · {{ a.material }}</div>
                <div class="ai-meta">
                  <span>{{ a.team_name }}</span>
                  <span class="dot">·</span>
                  <span>{{ a.stage_name }}</span>
                  <span class="dot">·</span>
                  <span class="ai-due">{{ a.due_date }}</span>
                </div>
              </div>
              <div v-if="alerts.overdue.length > 20" class="alert-more">等 {{ alerts.overdue.length }} 条</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="alert-card alert-soon">
            <div class="section-title">
              <span class="alert-title-warning">临期任务（3 天内）</span>
              <div class="title-right">
                <el-tag size="small" type="warning" round>{{ alerts.due_soon.length }}</el-tag>
                <el-button
                  v-if="alerts.due_soon.length && !isStaff"
                  size="small"
                  type="warning"
                  plain
                  :loading="reminding.due_soon"
                  @click="remind('due_soon')"
                >全部催办</el-button>
              </div>
            </div>
            <el-empty v-if="!alerts.due_soon.length" description="无临期" :image-size="60" />
            <div v-else class="alert-list">
              <div v-for="a in alerts.due_soon.slice(0, 20)" :key="a.task_id" class="alert-item alert-item-warning" @click="router.push('/projects/' + a.project_id)">
                <div class="ai-title">{{ a.project_name }} · {{ a.material }}</div>
                <div class="ai-meta">
                  <span>{{ a.team_name }}</span>
                  <span class="dot">·</span>
                  <span>{{ a.stage_name }}</span>
                  <span class="dot">·</span>
                  <span class="ai-due">{{ a.due_date }}</span>
                </div>
              </div>
              <div v-if="alerts.due_soon.length > 20" class="alert-more">等 {{ alerts.due_soon.length }} 条</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card shadow="never" class="alert-card alert-review">
            <div class="section-title">
              <span class="alert-title-primary">待审核</span>
              <div class="title-right">
                <el-tag size="small" type="primary" round>{{ alerts.pending_review.length }}</el-tag>
                <el-button
                  v-if="alerts.pending_review.length && !isStaff"
                  size="small"
                  type="primary"
                  plain
                  :loading="reminding.pending_review"
                  @click="remind('pending_review')"
                >全部催办</el-button>
              </div>
            </div>
            <el-empty v-if="!alerts.pending_review.length" description="无待审核" :image-size="60" />
            <div v-else class="alert-list">
              <div v-for="a in alerts.pending_review.slice(0, 20)" :key="a.task_id" class="alert-item alert-item-primary" @click="router.push('/projects/' + a.project_id)">
                <div class="ai-title">{{ a.project_name }} · {{ a.material }}</div>
                <div class="ai-meta">
                  <span>{{ a.team_name }}</span>
                  <span class="dot">·</span>
                  <span>{{ a.stage_name }}</span>
                </div>
              </div>
              <div v-if="alerts.pending_review.length > 20" class="alert-more">等 {{ alerts.pending_review.length }} 条</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- ============ 干事视图 ============ -->
    <template v-else>
      <el-card shadow="never" class="welcome">
        <div class="hello">你好,{{ auth.user?.name }} 👋</div>
        <div class="role">当前角色: {{ auth.role }}</div>
        <div class="desc">以下是你被指派的材料任务,请按时完成并上传。</div>
      </el-card>

      <el-row :gutter="16" class="stat-row">
        <el-col :xs="12" :sm="6" v-for="(s, i) in staffStats" :key="s.key">
          <el-card
            shadow="never"
            class="stat-card"
            :class="'stat-' + s.key"
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: i * 80 } }"
          >
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><component :is="s.icon" /></el-icon></div>
              <div class="stat-body">
                <div class="stat-num">{{ s.value }}</div>
                <div class="stat-label">{{ s.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="section-card">
        <div class="section-title"><span>我的待办任务</span><el-button link type="primary" @click="load">刷新</el-button></div>
        <el-empty v-if="!myTasks.length" description="暂无指派给你的任务" :image-size="80" />
        <el-table v-else :data="myTasks" stripe border @row-click="(r) => router.push('/projects/' + r.project_id)">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="project_name" label="项目" min-width="160" />
          <el-table-column prop="stage_name" label="阶段" width="110" />
          <el-table-column prop="team_name" label="团队" min-width="120" />
          <el-table-column prop="material" label="材料" min-width="140" />
          <el-table-column label="截止时间" width="150">
            <template #default="{ row }">
              <span :class="{ 'text-overdue': isTaskOverdue(row) }">{{ row.due_date || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="router.push('/projects/' + row.project_id)">去上传</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Warning, Clock, Document, Files, CircleCheck, Upload, CloseBold,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import * as dashboardApi from '@/api/dashboard'
import * as notificationsApi from '@/api/notifications'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const data = ref(null)
const alertRowRef = ref(null)

const isStaff = computed(() => auth.role === '干事')

const overview = computed(() => data.value?.overview || {})
const projects = computed(() => data.value?.projects || [])
const workload = computed(() => data.value?.workload || [])
const alerts = computed(() => data.value?.alerts || { overdue: [], due_soon: [], pending_review: [] })
const myTasks = computed(() => data.value?.my_tasks || [])

// 部长/副部长统计卡
const stats = computed(() => [
  { key: 'projects', label: '进行中项目', value: overview.value.projects_active || 0, icon: Files, scroll: '' },
  { key: 'pending', label: '待审核任务', value: overview.value.tasks_pending_review || 0, icon: Clock, scroll: 'review' },
  { key: 'overdue', label: '逾期任务', value: overview.value.tasks_overdue || 0, icon: Warning, scroll: 'overdue' },
  { key: 'soon', label: '临期任务(3天)', value: overview.value.tasks_due_soon || 0, icon: Document, scroll: 'soon' },
])

// 干事统计卡
const staffStats = computed(() => [
  { key: 'projects', label: '我的任务', value: overview.value.my_total || 0, icon: Files },
  { key: 'pending', label: '已提交待审', value: overview.value.my_submitted || 0, icon: Clock },
  { key: 'passed', label: '已通过', value: overview.value.my_passed || 0, icon: CircleCheck },
  { key: 'overdue', label: '逾期', value: overview.value.my_overdue || 0, icon: Warning },
])

function pct(done, total) {
  if (!total) return 0
  return Math.round((done / total) * 100)
}

function progColor(p) {
  if (p >= 100) return '#1ebf6f'
  if (p >= 60) return '#1664ff'
  if (p >= 30) return '#bd7e00'
  return '#f65159'
}

function wlWidth(total) {
  const max = Math.max(...workload.value.map((w) => w.total), 1)
  return Math.max(8, Math.round((total / max) * 100))
}

function isStageOverdue(st) {
  if (!st.due_date) return false
  // 简化:截止时间已过且阶段未完成
  const due = new Date(st.due_date.replace(' ', 'T'))
  return !isNaN(due) && due < new Date() && st.done < st.total
}

function isTaskOverdue(row) {
  if (!row.due_date || row.status === '已通过') return false
  const due = new Date(row.due_date.replace(' ', 'T'))
  return !isNaN(due) && due < new Date()
}

function statusTag(status) {
  return { '未交': 'info', '已提交': 'warning', '已通过': 'success', '已打回': 'danger' }[status] || 'info'
}

function scrollTo(key) {
  if (!key) return
  const map = { overdue: '.alert-overdue', soon: '.alert-soon', review: '.alert-review' }
  const el = document.querySelector(map[key])
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ---------- 批量催办 ----------
const reminding = ref({ overdue: false, due_soon: false, pending_review: false })

async function remind(category) {
  reminding.value[category] = true
  try {
    const res = await notificationsApi.remindTasks({ category })
    const parts = [`已发送 ${res.sent} 条提醒`]
    if (res.deduped) parts.push(`跳过 ${res.deduped} 条(最近已发)`)
    ElMessage.success(parts.join(','))
  } catch (e) {
    // 拦截器已弹错
  } finally {
    reminding.value[category] = false
  }
}

async function load() {
  loading.value = true
  try {
    data.value = await dashboardApi.getDashboard()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ---- 欢迎卡(干事) ---- */
.welcome .hello {
  font-size: 20px;
  font-weight: 600;
  color: #0c0d0e;
}
.welcome .role {
  color: #737a87;
  margin-top: 6px;
  font-size: 13px;
}
.welcome .desc {
  color: #42464e;
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.7;
}

/* ---- 统计卡片 ---- */
.stat-row {
  margin-bottom: 0;
}
.stat-card {
  border-radius: 12px;
  cursor: default;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.stat-card.clickable {
  cursor: pointer;
}
.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.stat-projects .stat-icon { background: #ebf1ff; color: #1664ff; }
.stat-pending .stat-icon { background: #fef8eb; color: #bd7e00; }
.stat-passed .stat-icon { background: #eef9f1; color: #1ebf6f; }
.stat-overdue .stat-icon { background: #fdf5f5; color: #f65159; }
.stat-soon .stat-icon { background: #fef8eb; color: #bd7e00; }
.stat-num {
  font-size: 28px;
  font-weight: 600;
  color: #0c0d0e;
  line-height: 1.1;
}
.stat-label {
  font-size: 12px;
  color: #737a87;
  margin-top: 4px;
}

/* ---- 区块卡片 ---- */
.section-card {
  border-radius: 12px;
}
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.section-title .el-tag {
  margin-left: 8px;
}
.title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ---- 项目卡片 ---- */
.proj-card {
  background: #ffffff;
  border: 1px solid #eaedf1;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
}
.proj-card:hover {
  border-color: #c5dbff;
  box-shadow: 0 4px 12px rgba(22, 100, 255, 0.08);
  transform: translateY(-1px);
}
.proj-head {
  margin-bottom: 12px;
}
.proj-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.proj-name {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
}
.proj-meta {
  color: #737a87;
  font-size: 12px;
  margin-top: 6px;
}
.dot {
  margin: 0 4px;
}
.proj-progress {
  margin-bottom: 12px;
}
.prog-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.prog-label {
  font-size: 12px;
  color: #42464e;
  font-weight: 500;
}
.prog-text {
  font-size: 12px;
  color: #737a87;
}
.stage-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px;
  background: #fafbfc;
  border-radius: 8px;
  margin-bottom: 12px;
}
.stage-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.stage-name {
  font-size: 12px;
  color: #42464e;
  display: flex;
  align-items: center;
  gap: 6px;
}
.stage-due {
  font-size: 11px;
  color: #737a87;
}
.stage-due.overdue {
  color: #f65159;
  font-weight: 500;
}
.proj-stats {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #737a87;
}
.ps-item b {
  color: #0c0d0e;
  font-weight: 600;
  margin-right: 2px;
}
.ps-over b { color: #f65159; }

/* ---- 人员负荷 ---- */
.workload-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.wl-item {
  display: grid;
  grid-template-columns: 160px 1fr 160px;
  gap: 14px;
  align-items: center;
}
.wl-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.wl-name {
  font-size: 13px;
  font-weight: 600;
  color: #0c0d0e;
}
.wl-bar-wrap {
  background: #f6f8fa;
  border-radius: 6px;
  height: 24px;
  overflow: hidden;
}
.wl-bar {
  height: 100%;
  background: linear-gradient(90deg, #6e9fff, #1664ff);
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  min-width: 60px;
  transition: width 0.3s ease;
}
.wl-bar-text {
  font-size: 11px;
  color: #ffffff;
  font-weight: 500;
  white-space: nowrap;
}
.wl-stats {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  font-size: 12px;
  color: #737a87;
}
.wl-stat b {
  color: #0c0d0e;
}
.wl-over {
  color: #f65159;
}
.wl-over b { color: #f65159; }

/* ---- 预警区 ---- */
.alert-row {
  margin-top: 0;
}
.alert-card {
  border-radius: 12px;
  height: 100%;
}
.alert-title-danger { color: #f65159; }
.alert-title-warning { color: #bd7e00; }
.alert-title-primary { color: #1664ff; }
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}
.alert-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  border: 1px solid transparent;
}
.alert-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}
.alert-item-danger {
  background: #fdf5f5;
  border-color: #ffecec;
}
.alert-item-warning {
  background: #fef8eb;
  border-color: #fff3dc;
}
.alert-item-primary {
  background: #ebf1ff;
  border-color: #e0ecff;
}
.ai-title {
  font-size: 13px;
  font-weight: 500;
  color: #0c0d0e;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ai-meta {
  font-size: 11px;
  color: #737a87;
}
.ai-due {
  color: #f65159;
}
.alert-more {
  text-align: center;
  font-size: 12px;
  color: #737a87;
  padding: 6px;
}

/* ---- 表格 ---- */
.text-overdue {
  color: #f65159;
  font-weight: 500;
}

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .wl-item {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  .wl-stats {
    justify-content: flex-start;
  }
}
</style>
