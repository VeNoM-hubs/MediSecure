import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment } from '@/types'
import { useToast } from '@/components/Toast'
import { Button, EmptyState, Input, PageHeader, Panel, StatusBadge } from '@/components/ui'

interface AppointmentPage {
  items: Appointment[]
  meta: { total: number }
}

export function AdminAppointmentsPage() {
  const { push } = useToast()
  const [items, setItems] = useState<Appointment[]>([])
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get<AppointmentPage>('/appointments', {
        params: { page_size: 100, status: status || undefined, q: q || undefined },
      })
      setItems(res.data.items)
      setError('')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function cancel(id: string) {
    if (!window.confirm('Admin cancel this appointment?')) return
    try {
      await api.delete(`/appointments/${id}`)
      push('Appointment cancelled', 'success')
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader title="Appointment management" subtitle="Search, filter, and cancel appointments." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel className="mb-6">
        <div className="grid gap-3 sm:grid-cols-3">
          <Input placeholder="Search" value={q} onChange={(e) => setQ(e.target.value)} />
          <select
            className="rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {['pending', 'confirmed', 'completed', 'cancelled', 'rejected'].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <Button type="button" onClick={() => void load()}>
            Apply
          </Button>
        </div>
      </Panel>
      <Panel>
        {loading ? (
          <EmptyState message="Loading…" />
        ) : items.length === 0 ? (
          <EmptyState message="No appointments." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {items.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-semibold">
                    {a.patient_name} → {a.doctor_name}
                  </p>
                  <p className="text-sm text-[var(--color-muted)]">
                    {new Date(a.scheduled_at).toLocaleString()} · {a.reason || 'No reason'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={a.status} />
                  {['pending', 'confirmed', 'scheduled'].includes(a.status) ? (
                    <Button variant="secondary" onClick={() => cancel(a.id)}>
                      Cancel
                    </Button>
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
