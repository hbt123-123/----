import http from './index'

export const listTeamFiles = (pid, tid) =>
  http.get(`/projects/${pid}/teams/${tid}/files`).then((r) => r.files)

export const uploadFiles = (pid, tid, formData) =>
  http.post(`/projects/${pid}/teams/${tid}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const deleteFile = (pid, tid, filename) =>
  http.delete(`/projects/${pid}/teams/${tid}/files/${encodeURIComponent(filename)}`)

export const fileDownloadUrl = (pid, tid, filename) =>
  `/api/projects/${pid}/teams/${tid}/files/${encodeURIComponent(filename)}`
