import http from './index'

export const listProjects = () =>
  http.get('/projects').then((r) => r.projects)

export const createProject = (data) =>
  http.post('/projects', data).then((r) => r.project)

export const getProject = (pid) => http.get(`/projects/${pid}`)
