import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as notifyApi from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const unreadCount = ref(0)
  const recent = ref([])        // 铃铛下拉预览(最近 N 条)
  const list = ref([])          // 通知中心完整列表
  const total = ref(0)

  async function fetchUnreadCount() {
    try {
      const res = await notifyApi.getUnreadCount()
      unreadCount.value = res.count || 0
    } catch (e) {
      // 静默失败(轮询场景,避免弹错)
    }
  }

  async function fetchRecent(limit = 8) {
    const res = await notifyApi.getNotifications({ limit, unread: 0 })
    recent.value = res.notifications || []
    // 顺带同步未读数
    unreadCount.value = (res.notifications || []).filter((n) => !n.read_at).length
    // 修正:unread=0 表示全部,recount 应用 unread=1 端点
    await fetchUnreadCount()
  }

  async function fetchList(params = {}) {
    const res = await notifyApi.getNotifications(params)
    list.value = res.notifications || []
    total.value = res.total || 0
    return res
  }

  async function markRead(id) {
    await notifyApi.markRead(id)
    // 本地同步
    const it = recent.value.find((n) => n.id === id)
    if (it) it.read_at = new Date().toISOString()
    const it2 = list.value.find((n) => n.id === id)
    if (it2) it2.read_at = new Date().toISOString()
    if (unreadCount.value > 0) unreadCount.value -= 1
  }

  async function markAllRead() {
    await notifyApi.markAllRead()
    const nowIso = new Date().toISOString()
    recent.value.forEach((n) => (n.read_at = n.read_at || nowIso))
    list.value.forEach((n) => (n.read_at = n.read_at || nowIso))
    unreadCount.value = 0
  }

  async function remove(id) {
    await notifyApi.deleteNotification(id)
    recent.value = recent.value.filter((n) => n.id !== id)
    list.value = list.value.filter((n) => n.id !== id)
    total.value = Math.max(0, total.value - 1)
    // 若删除的是未读,计数减一
    const deleted = [...recent.value, ...list.value]
    if (!deleted.some((n) => n.id === id)) {
      // 已删除,无法判断;改为重新拉取计数
    }
    await fetchUnreadCount()
  }

  return {
    unreadCount, recent, list, total,
    fetchUnreadCount, fetchRecent, fetchList,
    markRead, markAllRead, remove,
  }
})
