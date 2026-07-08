import http from './index'

export const listTeams = (pid) =>
  http.get(`/projects/${pid}/teams`).then((r) => r.teams)

export const createTeam = (pid, data) =>
  http.post(`/projects/${pid}/teams`, data).then((r) => r.team)

export const updateTeam = (pid, tid, data) =>
  http.put(`/projects/${pid}/teams/${tid}`, data).then((r) => r.team)

export const deleteTeam = (pid, tid) =>
  http.delete(`/projects/${pid}/teams/${tid}`)

export const importTeams = (pid, file) => {
  const form = new FormData()
  form.append('file', file)
  return http.post(`/projects/${pid}/teams/import`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
