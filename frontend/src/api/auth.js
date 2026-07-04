import http from './index'

export const candidates = () => http.get('/auth/candidates').then((r) => r.candidates)

export const login = (userId, password) =>
  http.post('/auth/login', { userId, password })

export const logout = () => http.post('/auth/logout')

export const me = () => http.get('/auth/me')

export const changePassword = (oldPassword, newPassword) =>
  http.post('/auth/change-password', { oldPassword, newPassword })
