<template>
  <div class="notifications-page">
    <el-card shadow="never" class="main-card">
      <div class="page-head">
        <div class="head-left">
          <span class="title">通知中心</span>
          <el-tag v-if="unreadCount > 0" size="small" type="danger" round>{{ unreadCount }} 未读</el-tag>
        </div>
        <div class="head-right">
          <el-radio-group v-model="filter" size="small" @change="load">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="unread">未读</el-radio-button>
          </el-radio-group>
          <el-button v-if="unreadCount > 0" size="small" type="primary" plain @click="onMarkAllRead">
            全部已读
          </el-button>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </div>

      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!list.length && !loading" description="暂无通知" :image-size="80" />
        <div v-else class="n-list">
          <div
            v-for="n in list"
            :key="n.id"
            class="n-item"
            :class="{ unread: !n.read_at, [`n-type-${n.type}`]: true }"
            @click="onItemClick(n)"
          >
            <div class="n-indicator" :class="`ind-${n.type}`"></div>
            <div class="n-body">
              <div class="n-title-row">
                <span class="n-title">{{ n.title }}</span>
                <el-tag v-if="!n.read_at" size="small" type="danger" effect="plain">未读</el-tag>
                <el-tag size="small" effect="plain" :type="typeTag(n.type)">{{ typeLabel(n.type) }}</el-tag>
              </div>
              <div class="n-content">{{ n.content }}</div>
              <div class="n-meta">
                <span>{{ formatTime(n.created_at) }}</span>
                <span v-if="n.from_kind === 'manual'" class="n-from">来自手动催办</span>
                <span v-else-if="n.from_kind === 'auto'" class="n-from">系统自动</span>
              </div>
            </div>
            <div class="n-actions" @click.stop>
              <el-button v-if="!n.read_at" link size="small" type="primary" @click="onMarkRead(n)">已读</el-button>
              <el-button link size="small" type="danger" @click="onDelete(n)">删除</el-button>
            </div>
          </div>
        </div>

        <div v-if="total > list.length" class="pagination-wrap">
          <el-pagination
            background
            layout="prev, pager, next, total"
            :total="total"
            :page-size="pageSize"
            :current-page="page"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNotificationsStore } from '@/stores/notifications'

const router = useRouter()
const store = useNotificationsStore()

const loading = ref(false)
const filter = ref('all')
const page = ref(1)
const pageSize = 20

const list = computed(() => store.list)
const total = computed(() => store.total)
const unreadCount = computed(() => store.unreadCount)

function typeLabel(t) {
  return { overdue: '逾期', due_soon: '临期', pending_review: '待审核', system: '系统' }[t] || t
}
function typeTag(t) {
  return { overdue: 'danger', due_soon: 'warning', pending_review: 'primary', system: 'info' }[t] || 'info'
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return iso
  const now = new Date()
  const diff = (now - d) / 1000  // 秒
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + ' 天前'
  return d.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

async function load() {
  loading.value = true
  try {
    const params = {
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    }
    if (filter.value === 'unread') params.unread = 1
    await store.fetchList(params)
  } finally {
    loading.value = false
  }
}

function onPageChange(p) {
  page.value = p
  load()
}

async function onItemClick(n) {
  if (!n.read_at) {
    try { await store.markRead(n.id) } catch (e) { /* ignore */ }
  }
  if (n.link) router.push(n.link)
}

async function onMarkRead(n) {
  try {
    await store.markRead(n.id)
    ElMessage.success('已标记为已读')
  } catch (e) { /* ignore */ }
}

async function onMarkAllRead() {
  try {
    await store.markAllRead()
    ElMessage.success('已全部标记为已读')
  } catch (e) { /* ignore */ }
}

async function onDelete(n) {
  try {
    await ElMessageBox.confirm('确定删除这条通知?', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await store.remove(n.id)
    ElMessage.success('已删除')
  } catch (e) { /* ignore */ }
}

onMounted(load)
</script>

<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
}
.main-card {
  border-radius: 12px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.head-left .title {
  font-size: 18px;
  font-weight: 600;
  color: #0c0d0e;
}
.head-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.list-wrap {
  min-height: 200px;
}
.n-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.n-item {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #eaedf1;
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
  background: #ffffff;
}
.n-item:hover {
  border-color: #c5dbff;
  box-shadow: 0 2px 8px rgba(22, 100, 255, 0.06);
}
.n-item.unread {
  background: #f6faff;
}
.n-indicator {
  width: 4px;
  border-radius: 2px;
  flex-shrink: 0;
}
.ind-overdue { background: #f65159; }
.ind-due_soon { background: #bd7e00; }
.ind-pending_review { background: #1664ff; }
.ind-system { background: #737a87; }
.n-body {
  flex: 1;
  min-width: 0;
}
.n-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.n-title {
  font-size: 14px;
  font-weight: 600;
  color: #0c0d0e;
}
.n-item.unread .n-title {
  color: #1664ff;
}
.n-content {
  font-size: 13px;
  color: #42464e;
  line-height: 1.6;
  margin-bottom: 6px;
  word-break: break-all;
}
.n-meta {
  font-size: 11px;
  color: #737a87;
  display: flex;
  gap: 12px;
}
.n-from {
  font-style: italic;
}
.n-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .page-head {
    flex-direction: column;
    align-items: stretch;
  }
  .head-right {
    justify-content: space-between;
  }
  .n-item {
    flex-direction: column;
    gap: 8px;
  }
  .n-indicator {
    width: 100%;
    height: 3px;
  }
  .n-actions {
    justify-content: flex-end;
  }
}
</style>