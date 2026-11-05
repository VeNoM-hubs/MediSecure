import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment, AuditLog, Doctor, MedicalRecord, NotificationItem, Stats } from '@/types'
import {
  Button,
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  Skeleton,
  StatCard,
  StatusBadge,
} from '@/components/ui'

function startOfTodayUtc() {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfTodayUtc() {
  const d = new Date()
  d.setHours(23, 59, 59, 999)
  return d
}

export function DashboardPage() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [records, setRecords] = useState<MedicalRecord[]>([])
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unread, setUnread] = useState(0)
  const [stats, setStats] = useState<Stats | null>(null)
  const [audit, setAudit] = useState<AuditLog[]>([])

  const load = useCallback(async () => {
    if (!user) return
    setLoading(true)
    setError('')
    try {
      const apptsRes = await api.get<{ items: Appointment[] }>('/appointments', {
        params: { page_size: 50 },
      })
      setAppointments(apptsRes.data.items)

      const [notes, count] = await Promise.all([
        api.get<NotificationItem[]>('/notifications'),
        api.get<{ unread_count: number }>('/notifications/unread-count'),
      ])
      setNotifications(notes.data.slice(0, 5))
      setUnread(count.data.unread_count)

      if (user.role === 'patient') {
        const [docs, recs] = await Promise.all([
          api.get<Doctor[]>('/doctors'),
          api.get<MedicalRecord[]>('/medical-records/mine'),
        ])
        setDoctors(docs.data.slice(0, 4))
        setRecords(recs.data.slice(0, 4))
      }

      if (user.role === 'admin') {
        const [s, logs] = await Promise.all([
          api.get<Stats>('/admin/dashboard'),
          api.get<AuditLog[]>('/admin/audit-logs', { params: { limit: 8 } }),
        ])
        setStats(s.data)
        setAudit(logs.data)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    void load()
  }, [load])

  const now = Date.now()
  const upcoming = useMemo(
    () =>
      appointments
        .filter((a) => new Date(a.scheduled_at).getTime() >= now && !['cancelled', 'rejected'].includes(a.status))
        .sort((a, b) => +new Date(a.scheduled_at) - +new Date(b.scheduled_at)),
    [appointments, now],
  )
  const recentPast = useMemo(
    () =>
      appointments
        .filter((a) => new Date(a.scheduled_at).getTime() < now)
        .sort((a, b) => +new Date(b.scheduled_at) - +new Date(a.scheduled_at))
        .slice(0, 5),
    [appointments, now],
  )
  const today = useMemo(() => {
    const start = startOfTodayUtc().getTime()
    const end = endOfTodayUtc().getTime()
    return appointments.filter((a) => {
      const t = new Date(a.scheduled_at).getTime()
      return t >= start && t <= end && !['cancelled', 'rejected'].includes(a.status)
    })
  }, [appointments])
  const pending = useMemo(() => appointments.filter((a) => a.status === 'pending'), [appointments])
  const completedCount = useMemo(
    () => appointments.filter((a) => a.status === 'completed').length,
    [appointments],
  )

  const firstName = user?.full_name.split(' ')[0] ?? 'user'

  if (loading) {
    return (
      <div>
        <PageHeader title={`Welcome, ${firstName}`} subtitle="Loading your workspace…" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="mt-6 h-48" />
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <PageHeader title={`Welcome, ${firstName}`} />
        <ErrorState message={error} onRetry={() => void load()} />
      </div>
    )
  }

  if (user?.role === 'patient') {
    return (
      <div>
        <PageHeader
          title={`Welcome, ${firstName}`}
          subtitle="Your synthetic care overview — appointments, doctors, and records."
          crumbs={[{ label: 'Home', to: '/dashboard' }, { label: 'Dashboard' }]}
          actions={
            <>
              <Link to="/doctors">
                <Button type="button">Book appointment</Button>
              </Link>
              <Link to="/records">
                <Button type="button" variant="secondary">
                  View records
                </Button>
              </Link>
            </>
          }
        />
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Upcoming" value={upcoming.length} />
          <StatCard label="Past visits" value={recentPast.length} />
          <StatCard label="Doctors listed" value={doctors.length} />
          <StatCard label="Unread alerts" value={unread} />
        </div>
        <div className="grid gap-6 xl:grid-cols-2">
          <Panel
            title="Upcoming appointments"
            action={
              <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/appointments">
                View all
              </Link>
            }
          >
            {upcoming.length === 0 ? (
              <EmptyState
                message="No upcoming appointments."
                action={
                  <Link to="/doctors">
                    <Button type="button" variant="secondary">
                      Find a doctor
                    </Button>
                  </Link>
                }
              />
            ) : (
              <AppointmentList items={upcoming.slice(0, 5)} nameKey="doctor_name" />
            )}
          </Panel>
          <Panel title="Recent appointments">
            {recentPast.length === 0 ? (
              <EmptyState message="No past appointments yet." />
            ) : (
              <AppointmentList items={recentPast} nameKey="doctor_name" />
            )}
          </Panel>
          <Panel
            title="Available doctors"
            action={
              <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/doctors">
                Directory
              </Link>
            }
          >
            {doctors.length === 0 ? (
              <EmptyState message="No doctors available." />
            ) : (
              <ul className="space-y-3">
                {doctors.map((d) => (
                  <li key={d.id} className="flex items-center justify-between gap-3 rounded-xl border border-[var(--color-line)] p-3">
                    <div>
                      <p className="font-medium">{d.full_name}</p>
                      <p className="text-sm text-[var(--color-muted)]">{d.specialization_name || 'General'}</p>
                    </div>
                    <Link to={`/doctors/${d.id}`}>
                      <Button type="button" variant="secondary">
                        Book
                      </Button>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
          <Panel
            title="Recent medical records"
            action={
              <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/records">
                All records
              </Link>
            }
          >
            {records.length === 0 ? (
              <EmptyState message="No medical records yet." />
            ) : (
              <ul className="divide-y divide-[var(--color-line)]">
                {records.map((r) => (
                  <li key={r.id} className="py-3">
                    <p className="font-medium">{r.title}</p>
                    <p className="text-sm text-[var(--color-muted)]">{new Date(r.record_date).toLocaleDateString()}</p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
          <Panel
            className="xl:col-span-2"
            title="Unread notifications"
            action={
              <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/notifications">
                Open inbox
              </Link>
            }
          >
            {notifications.filter((n) => !n.is_read).length === 0 ? (
              <EmptyState message="You're all caught up." />
            ) : (
              <ul className="divide-y divide-[var(--color-line)]">
                {notifications
                  .filter((n) => !n.is_read)
                  .slice(0, 5)
                  .map((n) => (
                    <li key={n.id} className="py-3">
                      <p className="font-medium">{n.title}</p>
                      <p className="text-sm text-[var(--color-muted)]">{n.message}</p>
                    </li>
                  ))}
              </ul>
            )}
          </Panel>
        </div>
      </div>
    )
  }

  if (user?.role === 'doctor') {
    return (
      <div>
        <PageHeader
          title={`Welcome, ${firstName}`}
          subtitle="Today's schedule, pending requests, and consultation activity."
          crumbs={[{ label: 'Home', to: '/dashboard' }, { label: 'Dashboard' }]}
          actions={
            <>
              <Link to="/availability">
                <Button type="button">Manage availability</Button>
              </Link>
              <Link to="/doctor/records">
                <Button type="button" variant="secondary">
                  Patient records
                </Button>
              </Link>
            </>
          }
        />
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Today" value={today.length} />
          <StatCard label="Upcoming" value={upcoming.length} />
          <StatCard label="Pending requests" value={pending.length} />
          <StatCard label="Completed (loaded)" value={completedCount} />
        </div>
        <div className="grid gap-6 xl:grid-cols-2">
          <Panel title="Today's appointments">
            {today.length === 0 ? (
              <EmptyState message="No appointments scheduled for today." />
            ) : (
              <AppointmentList items={today} nameKey="patient_name" />
            )}
          </Panel>
          <Panel
            title="Pending requests"
            action={
              <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/appointments">
                Review
              </Link>
            }
          >
            {pending.length === 0 ? (
              <EmptyState message="No pending requests." />
            ) : (
              <AppointmentList items={pending.slice(0, 5)} nameKey="patient_name" />
            )}
          </Panel>
          <Panel title="Upcoming">
            {upcoming.length === 0 ? (
              <EmptyState message="No upcoming appointments." />
            ) : (
              <AppointmentList items={upcoming.slice(0, 5)} nameKey="patient_name" />
            )}
          </Panel>
          <Panel title="Recent consultations">
            {recentPast.filter((a) => a.status === 'completed').length === 0 ? (
              <EmptyState message="No completed consultations in this view." />
            ) : (
              <AppointmentList
                items={recentPast.filter((a) => a.status === 'completed').slice(0, 5)}
                nameKey="patient_name"
              />
            )}
          </Panel>
        </div>
      </div>
    )
  }

  // Admin
  return (
    <div>
      <PageHeader
        title={`Welcome, ${firstName}`}
        subtitle="System overview from live MediSecure APIs."
        crumbs={[{ label: 'Home', to: '/dashboard' }, { label: 'Admin dashboard' }]}
        actions={
          <>
            <Link to="/admin/appointments">
              <Button type="button">Appointments</Button>
            </Link>
            <Link to="/admin/audit">
              <Button type="button" variant="secondary">
                Audit logs
              </Button>
            </Link>
          </>
        }
      />
      {stats ? (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Patients" value={stats.total_patients} />
          <StatCard label="Doctors" value={stats.total_doctors} />
          <StatCard label="Appointments" value={stats.total_appointments} />
          <StatCard label="Pending" value={stats.pending_appointments} />
          <StatCard label="Completed" value={stats.completed_appointments} />
          <StatCard label="Cancelled / rejected" value={stats.cancelled_appointments} />
          <StatCard label="Active users" value={stats.active_users} />
          <StatCard label="Security events (7d)" value={stats.recent_security_events} />
        </div>
      ) : null}
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel
          title="Recent appointments"
          action={
            <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/admin/appointments">
              Manage
            </Link>
          }
        >
          {appointments.length === 0 ? (
            <EmptyState message="No appointments found." />
          ) : (
            <AppointmentList items={appointments.slice(0, 6)} nameKey="patient_name" secondaryKey="doctor_name" />
          )}
        </Panel>
        <Panel
          title="Recent administrative activity"
          action={
            <Link className="text-sm font-medium text-[var(--color-brand)] hover:underline" to="/admin/audit">
              Full audit
            </Link>
          }
        >
          {audit.length === 0 ? (
            <EmptyState message="No audit events yet." />
          ) : (
            <ul className="divide-y divide-[var(--color-line)]">
              {audit.map((a) => (
                <li key={a.id} className="py-3">
                  <p className="font-medium">{a.action}</p>
                  <p className="text-sm text-[var(--color-muted)]">
                    {a.actor_email || 'system'} · {new Date(a.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}

function AppointmentList({
  items,
  nameKey,
  secondaryKey,
}: {
  items: Appointment[]
  nameKey: 'patient_name' | 'doctor_name'
  secondaryKey?: 'patient_name' | 'doctor_name'
}) {
  return (
    <ul className="divide-y divide-[var(--color-line)]">
      {items.map((a) => (
        <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
          <div>
            <p className="font-medium">
              {a[nameKey] || 'Appointment'}
              {secondaryKey && a[secondaryKey] ? ` · ${a[secondaryKey]}` : ''}
            </p>
            <p className="text-sm text-[var(--color-muted)]">{new Date(a.scheduled_at).toLocaleString()}</p>
          </div>
          <StatusBadge status={a.status} />
        </li>
      ))}
    </ul>
  )
}
