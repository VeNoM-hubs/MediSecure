import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '@/lib/api'
import { EmptyState, PageHeader, Panel, StatusBadge } from '@/components/ui'

interface ScheduleItem {
  id: string
  scheduled_at: string
  status: string
  patient_id: string
  reason?: string | null
}

export function SchedulePage() {
  const [items, setItems] = useState<ScheduleItem[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<ScheduleItem[]>('/doctors/me/schedule')
      .then((res) => setItems(res.data))
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  return (
    <div>
      <PageHeader title="My schedule" subtitle="Upcoming appointments assigned to you." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel>
        {items.length === 0 ? (
          <EmptyState message="No scheduled visits." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium">{new Date(item.scheduled_at).toLocaleString()}</p>
                  <p className="text-sm text-[var(--color-muted)]">{item.reason || 'No reason listed'}</p>
                </div>
                <StatusBadge status={item.status} />
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
