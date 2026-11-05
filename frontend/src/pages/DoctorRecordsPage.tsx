import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { api, getErrorMessage } from '@/lib/api'
import type { Appointment, MedicalRecord } from '@/types'
import { useToast } from '@/components/Toast'
import { Button, EmptyState, FieldError, Input, Label, PageHeader, Panel } from '@/components/ui'

const schema = z.object({
  patient_id: z.string().min(1),
  appointment_id: z.string().optional(),
  title: z.string().min(2),
  diagnosis: z.string().optional(),
  treatment: z.string().optional(),
  prescription_notes: z.string().optional(),
  notes: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

interface AppointmentPage {
  items: Appointment[]
}

export function DoctorRecordsPage() {
  const { push } = useToast()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [records, setRecords] = useState<MedicalRecord[]>([])
  const [selectedPatient, setSelectedPatient] = useState('')
  const [error, setError] = useState('')
  const form = useForm<FormValues>({ resolver: zodResolver(schema) })

  useEffect(() => {
    api
      .get<AppointmentPage>('/appointments', { params: { page_size: 50 } })
      .then((res) => setAppointments(res.data.items))
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  async function loadRecords(patientId: string) {
    setSelectedPatient(patientId)
    form.setValue('patient_id', patientId)
    try {
      const res = await api.get<MedicalRecord[]>(`/medical-records/patient/${patientId}`)
      setRecords(res.data)
      setError('')
    } catch (err) {
      setRecords([])
      setError(getErrorMessage(err))
    }
  }

  async function onCreate(values: FormValues) {
    try {
      await api.post('/medical-records', values)
      push('Consultation notes saved', 'success')
      form.reset({ patient_id: values.patient_id })
      await loadRecords(values.patient_id)
    } catch (err) {
      push(getErrorMessage(err), 'error')
    }
  }

  const authorizedPatients = Array.from(
    new Map(
      appointments
        .filter((a) => a.status !== 'cancelled' && a.status !== 'rejected')
        .map((a) => [a.patient_id, a]),
    ).values(),
  )

  return (
    <div>
      <PageHeader
        title="Patient records"
        subtitle="Access synthetic records only for patients with an authorized appointment."
      />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Authorized patients</h2>
          {authorizedPatients.length === 0 ? (
            <EmptyState message="No authorized patients yet." />
          ) : (
            <ul className="space-y-2">
              {authorizedPatients.map((a) => (
                <li key={a.patient_id}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                      selectedPatient === a.patient_id
                        ? 'border-[var(--color-brand)] bg-[var(--color-brand-soft)]'
                        : 'border-[var(--color-line)]'
                    }`}
                    onClick={() => void loadRecords(a.patient_id)}
                  >
                    {a.patient_name || a.patient_id}
                  </button>
                </li>
              ))}
            </ul>
          )}

          <h2 className="mb-3 mt-6 text-lg font-semibold">Add consultation notes</h2>
          <form className="space-y-3" onSubmit={form.handleSubmit(onCreate)}>
            <input type="hidden" {...form.register('patient_id')} />
            <div>
              <Label>Title</Label>
              <Input {...form.register('title')} />
              <FieldError message={form.formState.errors.title?.message} />
            </div>
            <div>
              <Label>Diagnosis (synthetic)</Label>
              <Input {...form.register('diagnosis')} />
            </div>
            <div>
              <Label>Treatment summary</Label>
              <Input {...form.register('treatment')} />
            </div>
            <div>
              <Label>Prescription notes (synthetic)</Label>
              <Input {...form.register('prescription_notes')} />
            </div>
            <div>
              <Label>Notes</Label>
              <Input {...form.register('notes')} />
            </div>
            <Button type="submit" disabled={!selectedPatient}>
              Save notes
            </Button>
          </form>
        </Panel>

        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Records</h2>
          {records.length === 0 ? (
            <EmptyState message="Select a patient to view records." />
          ) : (
            <ul className="space-y-3">
              {records.map((r) => (
                <li key={r.id} className="rounded-xl border border-[var(--color-line)] p-3">
                  <p className="font-semibold">{r.title}</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    {new Date(r.record_date).toLocaleString()}
                  </p>
                  {r.diagnosis ? <p className="mt-1 text-sm">Diagnosis: {r.diagnosis}</p> : null}
                  {r.treatment ? <p className="text-sm">Treatment: {r.treatment}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  )
}
