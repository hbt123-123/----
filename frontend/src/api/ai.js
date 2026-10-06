import http from './index'

// AI 请求可能较慢,单独放宽到 90s(覆盖 index.js 默认 30s)
export const checkCompleteness = (pid, data) =>
  http.post(`/projects/${pid}/ai/check`, data, { timeout: 90000 })

export const generateDraft = (pid, data) =>
  http.post(`/projects/${pid}/ai/draft`, data, { timeout: 90000 })

export const summarizeMaterial = (pid, data) =>
  http.post(`/projects/${pid}/ai/summarize`, data, { timeout: 90000 })
