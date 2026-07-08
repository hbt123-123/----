import http from './index'

export const listTemplates = () =>
  http.get('/templates').then((r) => r.templates)

export const getTemplate = (tid) =>
  http.get(`/templates/${tid}`).then((r) => r.template)

export const createTemplate = (data) =>
  http.post('/templates', data).then((r) => r.template)

export const updateTemplate = (tid, data) =>
  http.put(`/templates/${tid}`, data).then((r) => r.template)

export const cloneTemplate = (tid) =>
  http.post(`/templates/${tid}/clone`).then((r) => r.template)

export const deleteTemplate = (tid) => http.delete(`/templates/${tid}`)
