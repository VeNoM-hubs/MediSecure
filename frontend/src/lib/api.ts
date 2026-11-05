import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { AuthUser } from '@/types'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const STORAGE_KEY = 'medisecure_auth'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

function readAuth(): AuthUser | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

function writeAuth(next: AuthUser) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
}

function clearSessionAndRedirect() {
  localStorage.removeItem(STORAGE_KEY)
  const path = window.location.pathname
  if (!path.startsWith('/login') && !path.startsWith('/register')) {
    window.location.href = '/login?expired=1'
  }
}

let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const auth = readAuth()
  if (!auth?.refresh_token) return null

  // Use a bare client so the response interceptor cannot recurse.
  const { data } = await axios.post(
    `${baseURL}/auth/refresh`,
    { refresh_token: auth.refresh_token },
    { headers: { 'Content-Type': 'application/json' } },
  )

  const next: AuthUser = {
    ...auth,
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + (data.expires_in ?? 900) * 1000,
  }
  writeAuth(next)
  return next.access_token
}

api.interceptors.request.use((config) => {
  const auth = readAuth()
  if (auth?.access_token) {
    config.headers.Authorization = `Bearer ${auth.access_token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const status = error.response?.status
    const url = original?.url || ''

    if (
      status === 401 &&
      original &&
      !original._retry &&
      !url.includes('/auth/login') &&
      !url.includes('/auth/register') &&
      !url.includes('/auth/refresh')
    ) {
      original._retry = true
      try {
        refreshInFlight = refreshInFlight ?? refreshAccessToken()
        const token = await refreshInFlight
        refreshInFlight = null
        if (token) {
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        }
      } catch {
        refreshInFlight = null
        clearSessionAndRedirect()
        return Promise.reject(error)
      }
      clearSessionAndRedirect()
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
