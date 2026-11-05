import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { api, getErrorMessage } from '@/lib/api'
import type { PatientProfile } from '@/types'
import { Button, FieldError, Input, Label, PageHeader, Panel } from '@/components/ui'

const schema = z.object({
  full_name: z.string().min(2),
  phone: z.string().optional(),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  blood_type: z.string().optional(),
  address: z.string().optional(),
  emergency_contact: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

const passwordSchema = z.object({
  current_password: z.string().min(8),
  new_password: z.string().min(8),
})

type PasswordValues = z.infer<typeof passwordSchema>

export function ProfilePage() {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const form = useForm<FormValues>({ resolver: zodResolver(schema) })
  const pwForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema) })

  useEffect(() => {
    api
      .get<PatientProfile>('/patients/me')
      .then((res) => {
        form.reset({
          full_name: res.data.full_name,
          phone: res.data.phone || '',
          date_of_birth: res.data.date_of_birth || '',
          gender: res.data.gender || '',
          blood_type: res.data.blood_type || '',
          address: res.data.address || '',
          emergency_contact: res.data.emergency_contact || '',
        })
      })
      .catch((err) => setError(getErrorMessage(err)))
  }, [form])

  async function onSave(values: FormValues) {
    setError('')
    setMessage('')
    try {
      await api.put('/patients/me', values)
      setMessage('Profile updated.')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function onPassword(values: PasswordValues) {
    setError('')
    setMessage('')
    try {
      await api.post('/auth/change-password', values)
      setMessage('Password changed.')
      pwForm.reset()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title="My profile" subtitle="Update permitted personal details." />
      {error ? <p className="mb-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      {message ? <p className="mb-4 text-sm text-[var(--color-ok)]">{message}</p> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Personal details</h2>
          <form className="space-y-3" onSubmit={form.handleSubmit(onSave)}>
            {(
              [
                ['full_name', 'Full name'],
                ['phone', 'Phone'],
                ['date_of_birth', 'Date of birth'],
                ['gender', 'Gender'],
                ['blood_type', 'Blood type'],
                ['address', 'Address'],
                ['emergency_contact', 'Emergency contact'],
              ] as const
            ).map(([name, label]) => (
              <div key={name}>
                <Label>{label}</Label>
                <Input {...form.register(name)} />
                <FieldError message={form.formState.errors[name]?.message} />
              </div>
            ))}
            <Button type="submit">Save profile</Button>
          </form>
        </Panel>

        <Panel>
          <h2 className="mb-4 text-lg font-semibold">Change password</h2>
          <form className="space-y-3" onSubmit={pwForm.handleSubmit(onPassword)}>
            <div>
              <Label>Current password</Label>
              <Input type="password" {...pwForm.register('current_password')} />
              <FieldError message={pwForm.formState.errors.current_password?.message} />
            </div>
            <div>
              <Label>New password</Label>
              <Input type="password" {...pwForm.register('new_password')} />
              <FieldError message={pwForm.formState.errors.new_password?.message} />
            </div>
            <Button type="submit">Update password</Button>
          </form>
        </Panel>
      </div>
    </div>
  )
}
