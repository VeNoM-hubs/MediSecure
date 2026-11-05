import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Activity,
  Bell,
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Shield,
  Stethoscope,
  Users,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import type { Role } from '@/types'

const links: Record<Role, { to: string; label: string; icon: typeof LayoutDashboard }[]> = {
  patient: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/doctors', label: 'Doctors', icon: Stethoscope },
    { to: '/appointments', label: 'Appointments', icon: CalendarDays },
    { to: '/records', label: 'Records', icon: ClipboardList },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/profile', label: 'Profile', icon: Users },
  ],
  doctor: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/appointments', label: 'Appointments', icon: CalendarDays },
    { to: '/schedule', label: 'Schedule', icon: Activity },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  admin: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/patients', label: 'Patients', icon: Users },
    { to: '/admin/doctors', label: 'Doctors', icon: Stethoscope },
    { to: '/admin/specializations', label: 'Specializations', icon: Activity },
    { to: '/admin/audit', label: 'Audit & Security', icon: Shield },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
}

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null

  const nav = links[user.role]

  async function onLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-[var(--color-line)] bg-[var(--color-panel)]/90 backdrop-blur lg:border-b-0 lg:border-r">
        <div className="px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-brand)] text-white shadow-sm">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <p className="font-[family-name:var(--font-display)] text-xl font-semibold tracking-tight text-[var(--color-ink)]">
                MediSecure
              </p>
              <p className="text-xs uppercase tracking-[0.16em] text-[var(--color-muted)]">Healthcare portal</p>
            </div>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-4 lg:flex-col lg:overflow-visible">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-[var(--color-brand-soft)] text-[var(--color-brand-dark)]'
                    : 'text-[var(--color-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-ink)]'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="hidden border-t border-[var(--color-line)] px-6 py-5 lg:block">
          <p className="text-sm font-semibold">{user.full_name}</p>
          <p className="text-xs capitalize text-[var(--color-muted)]">{user.role}</p>
          <button
            type="button"
            onClick={onLogout}
            className="mt-3 inline-flex items-center gap-2 text-sm text-[var(--color-danger)] hover:underline"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>
      <main className="px-4 py-6 sm:px-8 lg:px-10">
        <div className="mb-6 flex items-center justify-between lg:hidden">
          <div>
            <p className="text-sm font-semibold">{user.full_name}</p>
            <p className="text-xs capitalize text-[var(--color-muted)]">{user.role}</p>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
        <Outlet />
      </main>
    </div>
  )
}
