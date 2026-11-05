import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '@/lib/api'
import { useToast } from '@/components/Toast'
import { Button, EmptyState, Input, Label, PageHeader, Panel } from '@/components/ui'

interface Slot {
  id: string
  starts_at: string
  ends_at: string
  is_booked: boolean
}

export function AvailabilityPage() {
  const { push } = useToast()
  const [slots, setSlots] = useState<Slot[]>([])
  const [startsAt, setStartsAt] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get<Slot[]>('/doctors/me/slots')
      setSlots(res.data)
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

  async function createSlot() {
    if (!startsAt) return
    try {
      await api.post('/doctors/me/slots', { starts_at: new Date(startsAt).toISOString() })
      push('Slot created', 'success')
      setStartsAt('')
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  async function removeSlot(id: string) {
    if (!window.confirm('Delete this open slot?')) return
    try {
      await api.delete(`/doctors/me/slots/${id}`)
      push('Slot deleted', 'success')
      await load()
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader title="Availability" subtitle="Create and manage open appointment slots (UTC stored)." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Add slot</h2>
          <Label>Starts at</Label>
          <Input type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} />
          <Button className="mt-3" type="button" onClick={() => void createSlot()}>
            Create slot
          </Button>
        </Panel>
        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Upcoming slots</h2>
          {loading ? (
            <EmptyState message="Loading…" />
          ) : slots.length === 0 ? (
            <EmptyState message="No upcoming slots." />
          ) : (
            <ul className="divide-y divide-[var(--color-line)]">
              {slots.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{new Date(s.starts_at).toLocaleString()}</p>
                    <p className="text-xs text-[var(--color-muted)]">{s.is_booked ? 'Booked' : 'Open'}</p>
                  </div>
                  {!s.is_booked ? (
                    <Button variant="secondary" onClick={() => removeSlot(s.id)}>
                      Delete
                    </Button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}
