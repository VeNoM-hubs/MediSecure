import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '@/context/AuthContext'
import { getErrorMessage } from '@/lib/api'
import { Button, FieldError, Input, Label, Panel } from '@/components/ui'

const schema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(8, 'Minimum 8 characters'),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [error, setError] = useState('')
  const sessionExpired = params.get('expired') === '1'
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormValues) {
    setError('')
    try {
      await login(values.email, values.password)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-10">
      <div className="mb-8 text-center animate-fade">
        <Link to="/" className="font-[family-name:var(--font-display)] text-3xl font-semibold text-[var(--color-ink)]">
          MediSecure
        </Link>
        <p className="mt-2 text-sm text-[var(--color-muted)]">Sign in to your secure portal</p>
      </div>
      <Panel>
        {sessionExpired ? (
          <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            Your session expired. Please sign in again.
          </p>
        ) : null}
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <Label>Email</Label>
            <Input type="email" autoComplete="email" {...register('email')} />
            <FieldError message={errors.email?.message} />
          </div>
          <div>
            <Label>Password</Label>
            <Input type="password" autoComplete="current-password" {...register('password')} />
            <FieldError message={errors.password?.message} />
          </div>
          {error ? <p className="text-sm text-[var(--color-danger)]">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          New patient?{' '}
          <Link className="font-semibold text-[var(--color-brand)] hover:underline" to="/register">
            Create an account
          </Link>
        </p>
        <p className="mt-3 text-center text-xs text-[var(--color-muted)]">
          Demo: bhaskar@gmail.com / 12345678
        </p>
      </Panel>
    </div>
  )
}
