import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment } from '@/types'
import { Button, EmptyState, PageHeader, Panel, StatusBadge } from '@/components/ui'

export function AppointmentsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Appointment[]>([])
  const [error, setError] = useState('')

  async function load() {
    try {
      const res = await api.get<Appointment[]>('/appointments/mine')
      setItems(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function cancel(id: string) {
    try {
      await api.post(`/appointments/${id}/cancel`)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function updateStatus(id: string, status: string) {
    try {
      await api.patch(`/appointments/${id}/status`, { status })
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title="Appointments" subtitle="Manage your scheduled visits." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel>
        {items.length === 0 ? (
          <EmptyState message="No appointments found." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {items.map((a) => (
              <li key={a.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold">
                    {user?.role === 'patient' ? a.doctor_name : a.patient_name}
                  </p>
                  <p className="text-sm text-[var(--color-muted)]">
                    {new Date(a.scheduled_at).toLocaleString()}
                    {a.reason ? ` · ${a.reason}` : ''}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={a.status} />
                  {user?.role === 'patient' && ['scheduled', 'confirmed'].includes(a.status) ? (
                    <Button variant="secondary" onClick={() => cancel(a.id)}>
                      Cancel
                    </Button>
                  ) : null}
                  {user?.role === 'doctor' && a.status !== 'cancelled' ? (
                    <>
                      <Button variant="secondary" onClick={() => updateStatus(a.id, 'confirmed')}>
                        Confirm
                      </Button>
                      <Button onClick={() => updateStatus(a.id, 'completed')}>Complete</Button>
                    </>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
