<template>
  <div class="public-projects">
    <!-- 顶部介绍 -->
    <el-card shadow="never" class="hero-card">
      <div class="hero">
        <div class="hero-text">
          <div class="hero-title">创新实践项目公开看板</div>
          <div class="hero-sub">
            浏览本部门公开项目的进度概览。详细信息(团队、材料、答辩成绩)仅对内部成员可见,请登录后查看。
          </div>
        </div>
        <div class="hero-stats">
          <div class="hs-item">
            <div class="hs-num">{{ overview.project_count }}</div>
            <div class="hs-label">公开项目</div>
          </div>
          <div class="hs-item">
            <div class="hs-num">{{ overview.team_count }}</div>
            <div class="hs-label">参与团队</div>
          </div>
          <div class="hs-item">
            <div class="hs-num">{{ overview.passed_rate }}%</div>
            <div class="hs-label">整体完成率</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索项目名称 / 模板 / 年份"
        clearable
        :prefix-icon="Search"
        class="kw-input"
      />
      <el-select v-model="yearFilter" placeholder="年份" clearable class="year-sel">
        <el-option v-for="y in yearOptions" :key="y" :label="y + ' 年'" :value="y" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态" clearable class="status-sel">
        <el-option label="进行中" value="进行中" />
        <el-option label="已结束" value="已结束" />
      </el-select>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <!-- 项目卡片网格 -->
    <div v-loading="loading" class="proj-grid">
      <el-empty
        v-if="!loading && !filtered.length"
        description="暂无公开项目"
        :image-size="100"
      />
      <div
        v-for="(p, i) in filtered"
        :key="p.id"
        class="proj-card"
        v-motion
        :initial="{ opacity: 0, y: 18 }"
        :enter="{ opacity: 1, y: 0, transition: { delay: Math.min(i * 50, 300) } }"
        @click="goDetail(p.id)"
      >
        <div class="pc-head">
          <span class="pc-name">{{ p.name }}</span>
          <el-tag size="small" :type="p.status === '进行中' ? 'success' : 'info'">{{ p.status }}</el-tag>
        </div>
        <div class="pc-meta">
          <span>{{ p.template_name }}</span>
          <span class="dot">·</span>
          <span>{{ p.year }} 年</span>
          <el-tag v-if="p.level" size="small" effect="plain" class="ml">{{ p.level }}</el-tag>
        </div>
        <div class="pc-stats">
          <span class="ps"><b>{{ p.team_count }}</b> 团队</span>
          <span class="ps"><b>{{ p.stage_count }}</b> 阶段</span>
        </div>
        <div class="pc-progress">
          <div class="pp-line">
            <span class="pp-label">材料进度</span>
            <span class="pp-text">{{ p.task_stats.passed }} / {{ p.task_stats.total }}</span>
          </div>
          <el-progress
            :percentage="pct(p.task_stats.passed, p.task_stats.total)"
            :stroke-width="6"
            :color="progColor(pct(p.task_stats.passed, p.task_stats.total))"
            :show-text="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import * as publicApi from '@/api/public'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const keyword = ref('')
const yearFilter = ref('')
const statusFilter = ref('')

const yearOptions = computed(() => {
  const set = new Set(projects.value.map((p) => p.year).filter(Boolean))
  return [...set].sort((a, b) => b.localeCompare(a))
})

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return projects.value.filter((p) => {
    if (yearFilter.value && p.year !== yearFilter.value) return false
    if (statusFilter.value && p.status !== statusFilter.value) return false
    if (kw) {
      const hay = `${p.name} ${p.template_name} ${p.year}`.toLowerCase()
      if (!hay.includes(kw)) return false
    }
    return true
  })
})

const overview = computed(() => {
  const ps = projects.value
  const project_count = ps.length
  const team_count = ps.reduce((s, p) => s + (p.team_count || 0), 0)
  const total = ps.reduce((s, p) => s + (p.task_stats?.total || 0), 0)
  const passed = ps.reduce((s, p) => s + (p.task_stats?.passed || 0), 0)
  const passed_rate = total ? Math.round((passed / total) * 100) : 0
  return { project_count, team_count, passed_rate }
})

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

function goDetail(id) {
  router.push(`/public/projects/${id}`)
}

async function load() {
  loading.value = true
  try {
    projects.value = await publicApi.listPublicProjects()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.public-projects {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Hero */
.hero-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #0c0d0e 0%, #1d2129 60%, #2b303a 100%);
  border: none;
  color: #ffffff;
}
.hero-card :deep(.el-card__body) {
  padding: 24px;
}
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}
.hero-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.hero-sub {
  margin-top: 8px;
  font-size: 13px;
  color: #c9cdd4;
  line-height: 1.6;
  max-width: 560px;
}
.hero-stats {
  display: flex;
  gap: 28px;
}
.hs-item {
  text-align: center;
}
.hs-num {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
}
.hs-label {
  font-size: 12px;
  color: #a0a2a7;
  margin-top: 4px;
}

/* Filter */
.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.kw-input {
  flex: 1;
  min-width: 220px;
}
.year-sel,
.status-sel {
  width: 130px;
}

/* Grid */
.proj-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  min-height: 80px;
}
.proj-card {
  background: #ffffff;
  border: 1px solid #eaedf1;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
}
.proj-card:hover {
  transform: translateY(-2px);
  border-color: #c5dbff;
  box-shadow: 0 6px 16px rgba(22, 100, 255, 0.08);
}
.pc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.pc-name {
  font-size: 15px;
  font-weight: 600;
  color: #0c0d0e;
  line-height: 1.4;
}
.pc-meta {
  font-size: 12px;
  color: #737a87;
  margin-bottom: 10px;
}
.pc-meta .ml {
  margin-left: 4px;
}
.dot {
  margin: 0 4px;
}
.pc-stats {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: #42464e;
  margin-bottom: 12px;
}
.pc-stats b {
  color: #0c0d0e;
  font-weight: 600;
  margin-right: 2px;
}
.pc-progress {
  margin-top: 4px;
}
.pp-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.pp-label {
  font-size: 12px;
  color: #42464e;
}
.pp-text {
  font-size: 12px;
  color: #737a87;
}

/* 响应式 */
@media (max-width: 767px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
  .hero-stats {
    gap: 20px;
    width: 100%;
    justify-content: space-between;
  }
  .proj-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 419px) {
  .hero-title {
    font-size: 17px;
  }
  .filter-bar .el-button {
    flex: 1;
  }
}
</style>