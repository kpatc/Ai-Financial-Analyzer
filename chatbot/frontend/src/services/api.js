import axios from 'axios'

const API_BASE = import.meta.env.DEV ? 'http://localhost:5000/api' : '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptors
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    throw error
  }
)

export const chatAPI = {
  send: (message, sessionId = 'default') =>
    api.post('/chat', { message, session_id: sessionId }),

  reset: (sessionId = 'default') =>
    api.post('/chat/reset', { session_id: sessionId }),

  getCompanies: () =>
    api.get('/companies'),

  getMetrics: (ticker) =>
    api.get(`/metrics/${ticker}`),

  getComparison: () =>
    api.get('/comparison'),

  search: (query) =>
    api.post('/search', { query }),

  health: () =>
    api.get('/health'),
}

export default api
