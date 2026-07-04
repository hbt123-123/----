import http from './index'

export const listUsers = () => http.get('/users').then((r) => r.users)

export const createUser = (data) => http.post('/users', data).then((r) => r.user)

export const updateUser = (uid, data) =>
  http.put(`/users/${uid}`, data).then((r) => r.user)

export const deleteUser = (uid) => http.delete(`/users/${uid}`)

export const resetPassword = (uid) => http.post(`/users/${uid}/reset-password`)

export const importUsers = (file) => {
  const form = new FormData()
  form.append('file', file)
  return http.post('/users/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
