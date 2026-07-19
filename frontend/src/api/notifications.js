import http from './index'

// 列表(可带 ?unread=1&limit=N&offset=M)
export const getNotifications = (params) => http.get('/notifications', { params })

// 60s 轮询用,极轻量
export const getUnreadCount = () => http.get('/notifications/unread-count')

// 标记单条已读
export const markRead = (id) => http.post(`/notifications/${id}/read`)

// 全部已读
export const markAllRead = () => http.post('/notifications/read-all')

// 删除单条
export const deleteNotification = (id) => http.delete(`/notifications/${id}`)

// 部长/副部长批量催办 { category, project_id?, task_ids? }
export const remindTasks = (data) => http.post('/notifications/remind', data)