import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getErrorMessage } from '@/lib/api'
import type { Doctor } from '@/types'
import { Button, EmptyState, PageHeader, Panel } from '@/components/ui'

export function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<Doctor[]>('/doctors')
      .then((res) => setDoctors(res.data))
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  return (
    <div>
      <PageHeader title="Find a doctor" subtitle="Browse specializations and open available slots." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}

      <Panel>
        <h2 className="mb-4 text-lg font-semibold">Available doctors</h2>
        {doctors.length === 0 ? (
          <EmptyState message="No doctors available." />
        ) : (
          <ul className="space-y-3">
            {doctors.map((d) => (
              <li key={d.id} className="rounded-xl border border-[var(--color-line)] p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">{d.full_name}</p>
                    <p className="text-sm text-[var(--color-muted)]">
                      {d.specialization_name || 'General'} · {d.years_experience} yrs
                    </p>
                    <p className="mt-1 text-sm text-[var(--color-muted)]">{d.bio}</p>
                  </div>
                  <Link to={`/doctors/${d.id}`}>
                    <Button type="button" variant="secondary">
                      View & book
                    </Button>
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
