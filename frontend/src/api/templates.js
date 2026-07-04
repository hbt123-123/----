import http from './index'

export const listTemplates = () =>
  http.get('/templates').then((r) => r.templates)

export const getTemplate = (tid) =>
  http.get(`/templates/${tid}`).then((r) => r.template)
