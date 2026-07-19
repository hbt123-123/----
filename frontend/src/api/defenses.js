import http from './index'

export const listDefenses = (pid) =>
  http.get(`/projects/${pid}/defenses`).then((r) => r.sessions)

export const createDefense = (pid, data) =>
  http.post(`/projects/${pid}/defenses`, data).then((r) => r.session)

export const updateDefense = (pid, sid, data) =>
  http.put(`/projects/${pid}/defenses/${sid}`, data).then((r) => r.session)

export const deleteDefense = (pid, sid) =>
  http.delete(`/projects/${pid}/defenses/${sid}`)
