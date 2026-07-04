import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const role = computed(() => user.value?.role || '')
  const isAdmin = computed(() => !!user.value?.is_admin)
  const isStaff = computed(() => role.value === '部长' || role.value === '副部长')

  async function fetchMe() {
    try {
      const res = await authApi.me()
      user.value = res.user
      return user.value
    } catch (e) {
      user.value = null
      return null
    } finally {
      ready.value = true
    }
  }

  async function login(userId, password) {
    const res = await authApi.login(userId, password)
    user.value = res.user
    return res
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
    }
  }

  function reset() {
    user.value = null
  }

  return { user, ready, isLoggedIn, role, isAdmin, isStaff, fetchMe, login, logout, reset }
})
