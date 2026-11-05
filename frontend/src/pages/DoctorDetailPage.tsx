import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { api, getErrorMessage } from '@/lib/api'
import type { Doctor } from '@/types'
import { useToast } from '@/components/Toast'
import { Button, EmptyState, FieldError, Label, PageHeader, Panel } from '@/components/ui'

interface Slot {
  id: string
  starts_at: string
  ends_at: string
  is_booked: boolean
}

const schema = z.object({
  slot_id: z.string().min(1, 'Select a slot'),
  reason: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function DoctorDetailPage() {
  const { doctorId } = useParams()
  const { push } = useToast()
  const [doctor, setDoctor] = useState<Doctor | null>(null)
  const [slots, setSlots] = useState<Slot[]>([])
  const [error, setError] = useState('')
  const form = useForm<FormValues>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (!doctorId) return
    Promise.all([
      api.get<Doctor>(`/doctors/${doctorId}`),
      api.get<Slot[]>(`/doctors/${doctorId}/availability`),
    ])
      .then(([d, s]) => {
        setDoctor(d.data)
        setSlots(s.data)
      })
      .catch((err) => setError(getErrorMessage(err)))
  }, [doctorId])

  async function onBook(values: FormValues) {
    const slot = slots.find((s) => s.id === values.slot_id)
    if (!slot || !doctorId) return
    try {
      await api.post('/appointments', {
        doctor_id: doctorId,
        slot_id: values.slot_id,
        scheduled_at: slot.starts_at,
        reason: values.reason,
      })
      push('Appointment requested', 'success')
      const refreshed = await api.get<Slot[]>(`/doctors/${doctorId}/availability`)
      setSlots(refreshed.data)
      form.reset()
    } catch (err) {
      const msg = getErrorMessage(err)
      setError(msg)
      push(msg, 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title={doctor?.full_name || 'Doctor'}
        subtitle={doctor?.specialization_name || 'Specialization'}
      />
      <p className="mb-4 text-sm">
        <Link className="text-[var(--color-brand)] hover:underline" to="/doctors">
          ← Back to directory
        </Link>
      </p>
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Profile</h2>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-[var(--color-muted)]">Experience</dt>
              <dd>{doctor?.years_experience ?? 0} years</dd>
            </div>
            <div>
              <dt className="text-[var(--color-muted)]">Qualifications</dt>
              <dd>{doctor?.qualifications || '—'}</dd>
            </div>
            <div>
              <dt className="text-[var(--color-muted)]">Availability</dt>
              <dd>{doctor?.availability_notes || '—'}</dd>
            </div>
            <div>
              <dt className="text-[var(--color-muted)]">Bio</dt>
              <dd>{doctor?.bio || '—'}</dd>
            </div>
          </dl>
        </Panel>

        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Book available slot</h2>
          {slots.length === 0 ? (
            <EmptyState message="No open slots right now." />
          ) : (
            <form className="space-y-3" onSubmit={form.handleSubmit(onBook)}>
              <div>
                <Label>Slot</Label>
                <select
                  className="w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm"
                  {...form.register('slot_id')}
                >
                  <option value="">Select</option>
                  {slots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {new Date(s.starts_at).toLocaleString()}
                    </option>
                  ))}
                </select>
                <FieldError message={form.formState.errors.slot_id?.message} />
              </div>
              <div>
                <Label>Reason</Label>
                <input
                  className="w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm"
                  {...form.register('reason')}
                />
              </div>
              <Button type="submit">Request appointment</Button>
            </form>
          )}
        </Panel>
      </div>
    </div>
  )
}
