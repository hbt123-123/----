import http from './index'

export const listTasks = (pid, params = {}) =>
  http.get(`/projects/${pid}/tasks`, { params }).then((r) => r.tasks)

export const generateTasks = (pid, data) =>
  http.post(`/projects/${pid}/tasks/generate`, data)

export const uploadTask = (pid, tid, file) => {
  const form = new FormData()
  form.append('file', file)
  return http
    .post(`/projects/${pid}/tasks/${tid}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.task)
}

export const reviewTask = (pid, tid, data) =>
  http.post(`/projects/${pid}/tasks/${tid}/review`, data).then((r) => r.task)

export const deleteTask = (pid, tid) =>
  http.delete(`/projects/${pid}/tasks/${tid}`)
