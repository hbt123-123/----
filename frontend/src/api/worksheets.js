import http from './index'

export const getWorksheet = (pid) =>
  http.get(`/projects/${pid}/worksheet`).then((r) => r.worksheet)

export const importWorksheet = (pid, file) => {
  const form = new FormData()
  form.append('file', file)
  return http
    .post(`/projects/${pid}/worksheet/import`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.worksheet)
}

export const saveWorksheet = (pid, data) =>
  http.put(`/projects/${pid}/worksheet`, data).then((r) => r.worksheet)

export const worksheetDownloadUrl = (pid) =>
  `/api/projects/${pid}/worksheet/download`
