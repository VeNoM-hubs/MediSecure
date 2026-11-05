import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { api } from '@/lib/api'
import type { AuthUser, Role } from '@/types'

interface AuthContextValue {
  user: AuthUser | null
  login: (email: string, password: string) => Promise<AuthUser>
  register: (payload: {
    email: string
    password: string
    full_name: string
    phone?: string
  }) => Promise<AuthUser>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)
const STORAGE_KEY = 'medisecure_auth'

function loadStored(): AuthUser | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

function toAuthUser(data: {
  access_token: string
  refresh_token: string
  user_id: string
  full_name: string
  role: Role
  expires_in?: number
}): AuthUser {
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    user_id: data.user_id,
    full_name: data.full_name,
    role: data.role,
    expires_at: Date.now() + (data.expires_in ?? 900) * 1000,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => loadStored())

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      async login(email, password) {
        const { data } = await api.post('/auth/login', { email, password })
        const next = toAuthUser(data)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
        setUser(next)
        return next
      },
      async register(payload) {
        const { data } = await api.post('/auth/register', payload)
        const next = toAuthUser(data)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
        setUser(next)
        return next
      },
      async logout() {
        try {
          await api.post('/auth/logout', { refresh_token: user?.refresh_token })
        } catch {
          /* still clear local session */
        }
        localStorage.removeItem(STORAGE_KEY)
        setUser(null)
      },
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
