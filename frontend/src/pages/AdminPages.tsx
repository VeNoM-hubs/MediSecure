import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { api, getErrorMessage } from '@/lib/api'
import type { AuditLog, Doctor, PatientProfile, Specialization } from '@/types'
import { Button, EmptyState, FieldError, Input, Label, PageHeader, Panel } from '@/components/ui'

export function AdminPatientsPage() {
  const [patients, setPatients] = useState<PatientProfile[]>([])
  const [error, setError] = useState('')

  async function load() {
    try {
      const res = await api.get<PatientProfile[]>('/admin/patients')
      setPatients(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function toggle(userId: string, isActive: boolean) {
    await api.patch(`/admin/users/${userId}/status`, { is_active: !isActive })
    await load()
  }

  return (
    <div>
      <PageHeader title="Patients" subtitle="Manage patient accounts. Passwords are never exposed." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <Panel>
        {patients.length === 0 ? (
          <EmptyState message="No patients." />
        ) : (
          <ul className="divide-y divide-[var(--color-line)]">
            {patients.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-semibold">{p.full_name}</p>
                  <p className="text-sm text-[var(--color-muted)]">{p.email}</p>
                </div>
                <Button variant="secondary" onClick={() => toggle(p.user_id, p.is_active)}>
                  {p.is_active ? 'Deactivate' : 'Activate'}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}

const doctorSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  full_name: z.string().min(2),
  specialization_id: z.string().optional(),
  license_number: z.string().optional(),
})

type DoctorForm = z.infer<typeof doctorSchema>

export function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [specs, setSpecs] = useState<Specialization[]>([])
  const [error, setError] = useState('')
  const form = useForm<DoctorForm>({ resolver: zodResolver(doctorSchema) })

  async function load() {
    const [d, s] = await Promise.all([
      api.get<Doctor[]>('/doctors'),
      api.get<Specialization[]>('/specializations'),
    ])
    setDoctors(d.data)
    setSpecs(s.data)
  }

  useEffect(() => {
    load().catch((err) => setError(getErrorMessage(err)))
  }, [])

  async function onCreate(values: DoctorForm) {
    setError('')
    try {
      await api.post('/doctors', values)
      form.reset()
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title="Doctors" subtitle="Provision clinician accounts and review the roster." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Add doctor</h2>
          <form className="space-y-3" onSubmit={form.handleSubmit(onCreate)}>
            <div>
              <Label>Full name</Label>
              <Input {...form.register('full_name')} />
              <FieldError message={form.formState.errors.full_name?.message} />
            </div>
            <div>
              <Label>Email</Label>
              <Input type="email" {...form.register('email')} />
              <FieldError message={form.formState.errors.email?.message} />
            </div>
            <div>
              <Label>Temporary password</Label>
              <Input type="password" {...form.register('password')} />
              <FieldError message={form.formState.errors.password?.message} />
            </div>
            <div>
              <Label>Specialization</Label>
              <select
                className="w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm"
                {...form.register('specialization_id')}
              >
                <option value="">Select</option>
                {specs.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>License number</Label>
              <Input {...form.register('license_number')} />
            </div>
            <Button type="submit">Create doctor</Button>
          </form>
        </Panel>
        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Roster</h2>
          <ul className="divide-y divide-[var(--color-line)]">
            {doctors.map((d) => (
              <li key={d.id} className="py-3">
                <p className="font-semibold">{d.full_name}</p>
                <p className="text-sm text-[var(--color-muted)]">
                  {d.email} · {d.specialization_name || 'Unassigned'}
                </p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  )
}

const specSchema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
})

type SpecForm = z.infer<typeof specSchema>

export function AdminSpecializationsPage() {
  const [specs, setSpecs] = useState<Specialization[]>([])
  const [error, setError] = useState('')
  const form = useForm<SpecForm>({ resolver: zodResolver(specSchema) })

  async function load() {
    const res = await api.get<Specialization[]>('/specializations')
    setSpecs(res.data)
  }

  useEffect(() => {
    load().catch((err) => setError(getErrorMessage(err)))
  }, [])

  async function onCreate(values: SpecForm) {
    try {
      await api.post('/specializations', values)
      form.reset()
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title="Specializations" subtitle="Maintain the clinical specialty catalog." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <form className="space-y-3" onSubmit={form.handleSubmit(onCreate)}>
            <div>
              <Label>Name</Label>
              <Input {...form.register('name')} />
              <FieldError message={form.formState.errors.name?.message} />
            </div>
            <div>
              <Label>Description</Label>
              <Input {...form.register('description')} />
            </div>
            <Button type="submit">Add specialization</Button>
          </form>
        </Panel>
        <Panel>
          <ul className="divide-y divide-[var(--color-line)]">
            {specs.map((s) => (
              <li key={s.id} className="py-3">
                <p className="font-semibold">{s.name}</p>
                <p className="text-sm text-[var(--color-muted)]">{s.description}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  )
}

export function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [security, setSecurity] = useState<AuditLog[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get<AuditLog[]>('/admin/audit-logs'),
      api.get<AuditLog[]>('/admin/security-events'),
    ])
      .then(([a, s]) => {
        setLogs(a.data)
        setSecurity(s.data)
      })
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  return (
    <div>
      <PageHeader title="Audit & security" subtitle="Immutable application events for monitoring and review." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Security events</h2>
          {security.length === 0 ? (
            <EmptyState message="No security events." />
          ) : (
            <ul className="max-h-[28rem] space-y-3 overflow-auto">
              {security.map((l) => (
                <li key={l.id} className="rounded-lg border border-[var(--color-line)] p-3 text-sm">
                  <p className="font-semibold">{l.action}</p>
                  <p className="text-[var(--color-muted)]">
                    {l.actor_email || 'system'} · {new Date(l.created_at).toLocaleString()}
                  </p>
                  {l.detail ? <p className="mt-1">{l.detail}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Audit log</h2>
          <ul className="max-h-[28rem] space-y-3 overflow-auto">
            {logs.map((l) => (
              <li key={l.id} className="rounded-lg border border-[var(--color-line)] p-3 text-sm">
                <p className="font-semibold">{l.action}</p>
                <p className="text-[var(--color-muted)]">
                  {l.actor_role}/{l.actor_email || 'n/a'} · {new Date(l.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  )
}
