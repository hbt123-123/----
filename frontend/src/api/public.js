import http from './index'

// 游客只读接口:不要求登录,失败不跳转登录页(http 拦截器对 /public/ 路径豁免)
export const listPublicProjects = () =>
  http.get('/public/projects').then((r) => r.projects)

export const getPublicProject = (pid) =>
  http.get(`/public/projects/${pid}`)
