<template>
  <el-container class="layout">
    <!-- 桌面端侧边栏：>=768px 显示 -->
    <el-aside :width="collapsed ? '64px' : '210px'" class="aside aside--desktop">
      <div class="logo">
        <span v-if="!collapsed">创实部管理平台</span>
        <span v-else>创实</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        router
        background-color="#0c0d0e"
        text-color="#c9cdd4"
        active-text-color="#1664ff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon><span>工作台</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/members">
          <el-icon><User /></el-icon><span>成员管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isStaff" index="/templates">
          <el-icon><Document /></el-icon><span>模板管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isStaff" index="/projects">
          <el-icon><Files /></el-icon><span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><Setting /></el-icon><span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 移动/平板端抽屉侧边栏：<768px 显示 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      :size="240"
      :show-close="false"
      :with-header="false"
      class="mobile-drawer"
    >
      <div class="drawer-logo">创实部管理平台</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#0c0d0e"
        text-color="#c9cdd4"
        active-text-color="#1664ff"
        @select="drawerVisible = false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon><span>工作台</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/members">
          <el-icon><User /></el-icon><span>成员管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isStaff" index="/templates">
          <el-icon><Document /></el-icon><span>模板管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isStaff" index="/projects">
          <el-icon><Files /></el-icon><span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><Setting /></el-icon><span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container>
      <el-header class="header">
        <!-- 桌面端折叠按钮 -->
        <el-icon class="collapse-btn collapse-btn--desktop" @click="collapsed = !collapsed">
          <Fold v-if="!collapsed" /><Expand v-else />
        </el-icon>
        <!-- 移动端菜单按钮 -->
        <el-icon class="collapse-btn collapse-btn--mobile" @click="drawerVisible = true">
          <Menu />
        </el-icon>
        <div class="spacer"></div>
        <!-- 通知铃铛 -->
        <el-popover
          :visible="bellVisible"
          placement="bottom-end"
          :width="380"
          trigger="click"
          @show="onBellShow"
        >
          <template #reference>
            <el-badge
              :value="notifications.unreadCount"
              :hidden="notifications.unreadCount === 0"
              :max="99"
              class="bell-badge"
            >
              <el-button circle class="bell-btn" aria-label="通知">
                <el-icon><Bell /></el-icon>
              </el-button>
            </el-badge>
          </template>
          <div class="bell-panel">
            <div class="bell-head">
              <span class="bell-title">通知</span>
              <el-button
                v-if="notifications.unreadCount > 0"
                link
                size="small"
                type="primary"
                @click="onBellMarkAllRead"
              >全部已读</el-button>
            </div>
            <div class="bell-list">
              <div
                v-for="n in notifications.recent"
                :key="n.id"
                class="bell-item"
                :class="{ unread: !n.read_at, [`bi-type-${n.type}`]: true }"
                @click="onBellItemClick(n)"
              >
                <div class="bi-indicator" :class="`ind-${n.type}`"></div>
                <div class="bi-body">
                  <div class="bi-title">{{ n.title }}</div>
                  <div class="bi-content">{{ n.content }}</div>
                  <div class="bi-time">{{ formatRelative(n.created_at) }}</div>
                </div>
              </div>
              <el-empty
                v-if="!notifications.recent.length"
                description="暂无通知"
                :image-size="40"
              />
            </div>
            <div class="bell-foot" @click="goAllNotifications">查看全部</div>
          </div>
        </el-popover>
        <el-dropdown @command="onCommand">
          <span class="user-trigger">
            {{ auth.user?.name || '用户' }}
            <el-tag size="small" effect="plain" type="info">{{ auth.role }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" v-if="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const notifications = useNotificationsStore()
const collapsed = ref(false)
const drawerVisible = ref(false)
const bellVisible = ref(false)
let pollTimer = null

async function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    await auth.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

// ---------- 通知铃铛 ----------
async function onBellShow() {
  await notifications.fetchRecent(8)
}
async function onBellItemClick(n) {
  if (!n.read_at) {
    try { await notifications.markRead(n.id) } catch (e) { /* ignore */ }
  }
  bellVisible.value = false
  if (n.link) router.push(n.link)
}
async function onBellMarkAllRead() {
  try {
    await notifications.markAllRead()
    ElMessage.success('已全部标记为已读')
  } catch (e) { /* ignore */ }
}
function goAllNotifications() {
  bellVisible.value = false
  router.push('/notifications')
}

function formatRelative(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return iso
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + ' 天前'
  return d.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

onMounted(() => {
  notifications.fetchUnreadCount()
  // 60s 轮询未读数;标签后台时暂停
  pollTimer = setInterval(() => {
    if (!document.hidden) notifications.fetchUnreadCount()
  }, 60000)
})
onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.bell-badge {
  margin-right: 16px;
}
.bell-btn {
  background: transparent;
  border: none;
  color: #42464e;
  font-size: 18px;
}
.bell-btn:hover {
  color: #1664ff;
}
.bell-panel {
  margin: -4px -8px;
}
.bell-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #eaedf1;
}
.bell-title {
  font-size: 14px;
  font-weight: 600;
  color: #0c0d0e;
}
.bell-list {
  max-height: 380px;
  overflow-y: auto;
  padding: 6px 0;
}
.bell-item {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.bell-item:hover {
  background: #f6faff;
}
.bell-item.unread {
  background: #f6faff;
  border-left-color: #1664ff;
}
.bi-indicator {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  margin-top: 4px;
  align-self: stretch;
  min-height: 16px;
}
.ind-overdue { background: #f65159; }
.ind-due_soon { background: #bd7e00; }
.ind-pending_review { background: #1664ff; }
.ind-system { background: #737a87; }
.bi-body {
  flex: 1;
  min-width: 0;
}
.bi-title {
  font-size: 13px;
  font-weight: 500;
  color: #0c0d0e;
  margin-bottom: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bi-content {
  font-size: 12px;
  color: #42464e;
  line-height: 1.5;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.bi-time {
  font-size: 11px;
  color: #737a87;
}
.bell-foot {
  padding: 10px 14px;
  text-align: center;
  font-size: 13px;
  color: #1664ff;
  cursor: pointer;
  border-top: 1px solid #eaedf1;
}
.bell-foot:hover {
  background: #f6faff;
}
</style>