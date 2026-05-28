import axios from 'axios'
import { useUserStore } from '../stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

api.interceptors.request.use(config => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = userStore.token
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
    }
    return Promise.reject(err)
  }
)

// 用户
export const login = (data) => api.post('/user/login', data)
export const register = (data) => api.post('/user/register', data)

// 牌桌
export const createTable = (data) => api.post('/table/create', data)

// 游戏
export const startGame = (data) => api.post('/game/start', data)
export const gameAction = (data) => api.post('/game/action', data)
export const gameSubmit = (data) => api.post('/game/submit', data)
export const gameSettle = (data) => api.post('/game/settle', data)

export default api