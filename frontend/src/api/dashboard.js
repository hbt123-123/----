import http from './index'

export const getDashboard = () => http.get('/dashboard')
