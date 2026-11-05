import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '@/context/AuthContext'
import { getErrorMessage } from '@/lib/api'
import { Button, FieldError, Input, Label, Panel } from '@/components/ui'

const schema = z.object({
  full_name: z.string().min(2, 'Name is required'),
  email: z.string().email('Valid email required'),
  phone: z.string().optional(),
  password: z.string().min(8, 'Minimum 8 characters'),
})

type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormValues) {
    setError('')
    try {
      await registerUser(values)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-10">
      <div className="mb-8 text-center animate-fade">
        <Link to="/" className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          MediSecure
        </Link>
        <p className="mt-2 text-sm text-[var(--color-muted)]">Patient registration (synthetic data only)</p>
      </div>
      <Panel>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <Label>Full name</Label>
            <Input {...register('full_name')} />
            <FieldError message={errors.full_name?.message} />
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" {...register('email')} />
            <FieldError message={errors.email?.message} />
          </div>
          <div>
            <Label>Phone (optional)</Label>
            <Input {...register('phone')} />
          </div>
          <div>
            <Label>Password</Label>
            <Input type="password" {...register('password')} />
            <FieldError message={errors.password?.message} />
          </div>
          {error ? <p className="text-sm text-[var(--color-danger)]">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating…' : 'Create account'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          Already registered?{' '}
          <Link className="font-semibold text-[var(--color-brand)] hover:underline" to="/login">
            Sign in
          </Link>
        </p>
      </Panel>
    </div>
  )
}
