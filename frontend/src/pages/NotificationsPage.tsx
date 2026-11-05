import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '@/lib/api'
import type { NotificationItem } from '@/types'
import { Button, EmptyState, PageHeader, Panel } from '@/components/ui'

export function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([])
  const [error, setError] = useState('')

  async function load() {
    try {
      const res = await api.get<NotificationItem[]>('/notifications')
      setItems(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function markRead(id: string) {
    await api.post(`/notifications/${id}/read`)
    await load()
  }

  return (
    <div>
      <PageHeader title="Notifications" subtitle="System and appointment updates for your account." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel>
        {items.length === 0 ? (
          <EmptyState message="No notifications." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {items.map((n) => (
              <li key={n.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className={`font-semibold ${n.is_read ? 'text-[var(--color-muted)]' : ''}`}>{n.title}</p>
                  <p className="text-sm text-[var(--color-muted)]">{n.message}</p>
                  <p className="mt-1 text-xs text-[var(--color-muted)]">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.is_read ? (
                  <Button variant="secondary" onClick={() => markRead(n.id)}>
                    Mark read
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
