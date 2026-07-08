import http from './index'

export const previewSummary = (pid) =>
  http.get(`/projects/${pid}/export/preview`)

export const summaryDownloadUrl = (pid) =>
  `/api/projects/${pid}/export/download`
