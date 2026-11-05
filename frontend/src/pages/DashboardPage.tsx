import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment, Stats } from '@/types'
import { EmptyState, PageHeader, Panel, StatusBadge } from '@/components/ui'

export function DashboardPage() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const appts = await api.get<Appointment[]>('/appointments/mine')
        setAppointments(appts.data.slice(0, 5))
        if (user?.role === 'admin') {
          const s = await api.get<Stats>('/admin/dashboard')
          setStats(s.data)
        }
      } catch (err) {
        setError(getErrorMessage(err))
      }
    }
    void load()
  }, [user?.role])

  return (
    <div>
      <PageHeader
        title={`Welcome, ${user?.full_name.split(' ')[0] ?? 'user'}`}
        subtitle="Synthetic healthcare workspace with role-based access and audit logging."
      />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}

      {user?.role === 'admin' && stats ? (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {[
            ['Patients', stats.total_patients],
            ['Doctors', stats.total_doctors],
            ['Appointments', stats.total_appointments],
            ['Active users', stats.active_users],
            ['Security events (7d)', stats.recent_security_events],
          ].map(([label, value]) => (
            <Panel key={String(label)} className="!p-4">
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--color-muted)]">{label}</p>
              <p className="mt-2 text-3xl font-bold text-[var(--color-ink)]">{value}</p>
            </Panel>
          ))}
        </div>
      ) : null}

      <Panel>
        <h2 className="mb-4 text-lg font-semibold">Recent appointments</h2>
        {appointments.length === 0 ? (
          <EmptyState message="No appointments yet." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {appointments.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium">
                    {user?.role === 'patient' ? a.doctor_name : a.patient_name || 'Appointment'}
                  </p>
                  <p className="text-sm text-[var(--color-muted)]">
                    {new Date(a.scheduled_at).toLocaleString()}
                  </p>
                </div>
                <StatusBadge status={a.status} />
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
