import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  Bell,
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Shield,
  Stethoscope,
  Users,
  X,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
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
    { to: '/availability', label: 'Availability', icon: Activity },
    { to: '/doctor/records', label: 'Patient records', icon: ClipboardList },
    { to: '/schedule', label: 'Schedule', icon: CalendarDays },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  admin: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/appointments', label: 'Appointments', icon: CalendarDays },
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
  const location = useLocation()
  const [unread, setUnread] = useState(0)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    if (!user) return
    api
      .get<{ unread_count: number }>('/notifications/unread-count')
      .then((res) => setUnread(res.data.unread_count))
      .catch(() => setUnread(0))
  }, [user, location.pathname])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  if (!user) return null

  const nav = links[user.role]

  async function onLogout() {
    await logout()
    navigate('/login')
  }

  const navContent = (
    <nav aria-label="Primary" className="flex flex-col gap-1 px-3 pb-4">
      {nav.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand)] ${
              isActive
                ? 'bg-[var(--color-brand-soft)] text-[var(--color-brand-dark)]'
                : 'text-[var(--color-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-ink)]'
            }`
          }
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
          <span className="flex-1">{label}</span>
          {to === '/notifications' && unread > 0 ? (
            <span className="rounded-md bg-[var(--color-brand)] px-1.5 py-0.5 text-[10px] font-bold text-white" aria-label={`${unread} unread`}>
              {unread}
            </span>
          ) : null}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="hidden border-r border-[var(--color-line)] bg-[var(--color-panel)]/90 backdrop-blur lg:flex lg:flex-col">
        <div className="px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-brand)] text-white shadow-sm" aria-hidden="true">
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
        {navContent}
        <div className="mt-auto border-t border-[var(--color-line)] px-6 py-5">
          <p className="text-sm font-semibold">{user.full_name}</p>
          <p className="text-xs capitalize text-[var(--color-muted)]">{user.role}</p>
          <button
            type="button"
            onClick={onLogout}
            className="mt-3 inline-flex items-center gap-2 rounded text-sm text-[var(--color-danger)] hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-[var(--color-line)] bg-[var(--color-panel)]/95 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-lg border border-[var(--color-line)] p-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]"
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav"
              onClick={() => setMobileOpen((v) => !v)}
            >
              {mobileOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
              <span className="sr-only">Toggle navigation</span>
            </button>
            <p className="font-[family-name:var(--font-display)] text-lg font-semibold">MediSecure</p>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </button>
        </header>

        {mobileOpen ? (
          <div id="mobile-nav" className="border-b border-[var(--color-line)] bg-[var(--color-panel)] lg:hidden">
            <div className="px-4 py-3">
              <p className="text-sm font-semibold">{user.full_name}</p>
              <p className="text-xs capitalize text-[var(--color-muted)]">{user.role}</p>
            </div>
            {navContent}
          </div>
        ) : null}

        <main id="main-content" className="px-4 py-6 sm:px-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
