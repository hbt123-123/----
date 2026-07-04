import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,
})

let authResetting = false

http.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data && typeof data === 'object' && 'error' in data) {
      ElMessage.error(data.error)
      return Promise.reject(new Error(data.error))
    }
    return data
  },
  (err) => {
    const status = err.response?.status
    const msg = err.response?.data?.error || err.message || '请求失败'
    if (status === 401 && !err.config?.url?.includes('/auth/')) {
      // 会话失效:清状态跳登录(避免登录接口本身 401 循环)
      if (!authResetting) {
        authResetting = true
        import('@/stores/auth').then(({ useAuthStore }) => {
          const auth = useAuthStore()
          auth.reset()
          authResetting = false
          if (location.hash !== '#/login' && location.pathname !== '/login') {
            location.href = '/login'
          }
        })
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default http
