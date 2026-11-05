import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const raw = localStorage.getItem('medisecure_auth')
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as { access_token?: string }
      if (parsed.access_token) {
        config.headers.Authorization = `Bearer ${parsed.access_token}`
      }
    } catch {
      /* ignore corrupt storage */
    }
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('medisecure_auth')
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Unexpected error'
}
