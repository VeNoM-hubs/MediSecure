import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import type { Role } from '@/types'

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, isAuthenticated } = useAuth()
  if (!isAuthenticated || !user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}
