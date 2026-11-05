import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '@/lib/api'
import type { MedicalRecord } from '@/types'
import { EmptyState, PageHeader, Panel } from '@/components/ui'

export function RecordsPage() {
  const [records, setRecords] = useState<MedicalRecord[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<MedicalRecord[]>('/medical-records/mine')
      .then((res) => setRecords(res.data))
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  return (
    <div>
      <PageHeader
        title="Medical records"
        subtitle="Fictional clinical summaries associated with your account."
      />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel>
        {records.length === 0 ? (
          <EmptyState message="No medical records yet." />
        ) : (
          <ul className="space-y-4">
            {records.map((r) => (
              <li key={r.id} className="rounded-xl border border-[var(--color-line)] p-4">
                <p className="font-semibold">{r.title}</p>
                <p className="text-xs text-[var(--color-muted)]">
                  {new Date(r.record_date).toLocaleDateString()}
                </p>
                {r.diagnosis ? <p className="mt-2 text-sm">Diagnosis: {r.diagnosis}</p> : null}
                {r.treatment ? <p className="text-sm">Treatment: {r.treatment}</p> : null}
                {r.notes ? <p className="mt-1 text-sm text-[var(--color-muted)]">{r.notes}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
