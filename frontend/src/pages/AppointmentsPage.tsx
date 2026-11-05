import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useToast } from '@/components/Toast'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment } from '@/types'
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  Label,
  PageHeader,
  Panel,
  Select,
  Spinner,
  StatusBadge,
} from '@/components/ui'

interface AppointmentPage {
  items: Appointment[]
  meta: { page: number; page_size: number; total: number; total_pages: number }
}

export function AppointmentsPage() {
  const { user } = useAuth()
  const { push } = useToast()
  const [items, setItems] = useState<Appointment[]>([])
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [upcoming, setUpcoming] = useState<'all' | 'upcoming' | 'past'>('all')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirmId, setConfirmId] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const params: Record<string, string | boolean | number> = { page: 1, page_size: 50 }
      if (status) params.status = status
      if (q) params.q = q
      if (upcoming === 'upcoming') params.upcoming = true
      if (upcoming === 'past') params.upcoming = false
      const res = await api.get<AppointmentPage>('/appointments', { params })
      setItems(res.data.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function cancelConfirmed() {
    if (!confirmId) return
    try {
      await api.post(`/appointments/${confirmId}/cancel`)
      push('Appointment cancelled', 'success')
      setConfirmId(null)
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function updateStatus(id: string, next: string) {
    try {
      await api.patch(`/appointments/${id}/status`, {
        status: next,
        consultation_notes: notes[id] || undefined,
      })
      push(`Marked ${next}`, 'success')
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title="Appointments"
        subtitle="Filter and manage appointments for your role."
        crumbs={[{ label: 'Home', to: '/dashboard' }, { label: 'Appointments' }]}
      />

      <Panel className="mb-6">
        <form
          className="grid gap-3 sm:grid-cols-4"
          onSubmit={(e) => {
            e.preventDefault()
            void load()
          }}
        >
          <div>
            <Label htmlFor="appt-search">Search</Label>
            <Input
              id="appt-search"
              placeholder="Name or reason"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="appt-status">Status</Label>
            <Select id="appt-status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All statuses</option>
              {['pending', 'confirmed', 'completed', 'cancelled', 'rejected'].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="appt-when">Timeframe</Label>
            <Select
              id="appt-when"
              value={upcoming}
              onChange={(e) => setUpcoming(e.target.value as 'all' | 'upcoming' | 'past')}
            >
              <option value="all">All times</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
            </Select>
          </div>
          <div className="flex items-end">
            <Button type="submit" className="w-full">
              Apply filters
            </Button>
          </div>
        </form>
      </Panel>

      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}

      <Panel>
        {loading ? (
          <Spinner label="Loading appointments" />
        ) : items.length === 0 ? (
          <EmptyState message="No appointments found." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {items.map((a) => (
              <li key={a.id} className="flex flex-col gap-3 py-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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
                    {(user?.role === 'patient' || user?.role === 'admin') &&
                    ['scheduled', 'confirmed', 'pending'].includes(a.status) ? (
                      <Button variant="secondary" onClick={() => setConfirmId(a.id)}>
                        Cancel
                      </Button>
                    ) : null}
                    {user?.role === 'doctor' && a.status === 'pending' ? (
                      <>
                        <Button variant="secondary" onClick={() => updateStatus(a.id, 'confirmed')}>
                          Accept
                        </Button>
                        <Button variant="danger" onClick={() => updateStatus(a.id, 'rejected')}>
                          Reject
                        </Button>
                      </>
                    ) : null}
                    {user?.role === 'doctor' && a.status === 'confirmed' ? (
                      <Button onClick={() => updateStatus(a.id, 'completed')}>Complete</Button>
                    ) : null}
                  </div>
                </div>
                {user?.role === 'doctor' && ['pending', 'confirmed'].includes(a.status) ? (
                  <div>
                    <Label htmlFor={`notes-${a.id}`}>Consultation notes</Label>
                    <Input
                      id={`notes-${a.id}`}
                      placeholder="Optional synthetic notes"
                      value={notes[a.id] || ''}
                      onChange={(e) => setNotes((prev) => ({ ...prev, [a.id]: e.target.value }))}
                    />
                  </div>
                ) : null}
                {a.consultation_notes ? (
                  <p className="text-sm text-[var(--color-muted)]">Notes: {a.consultation_notes}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <ConfirmDialog
        open={Boolean(confirmId)}
        title="Cancel appointment?"
        message="This cannot be undone from the patient portal. The doctor will be notified."
        confirmLabel="Cancel appointment"
        danger
        onCancel={() => setConfirmId(null)}
        onConfirm={() => void cancelConfirmed()}
      />
    </div>
  )
}
