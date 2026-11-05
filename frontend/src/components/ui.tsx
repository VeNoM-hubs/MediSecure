import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  PropsWithChildren,
  ReactNode,
  SelectHTMLAttributes,
} from 'react'
import { Link } from 'react-router-dom'

export function PageHeader({
  title,
  subtitle,
  actions,
  crumbs,
}: {
  title: string
  subtitle?: string
  actions?: ReactNode
  crumbs?: { label: string; to?: string }[]
}) {
  return (
    <header className="mb-8 animate-rise">
      {crumbs && crumbs.length > 0 ? (
        <nav aria-label="Breadcrumb" className="mb-3">
          <ol className="flex flex-wrap items-center gap-1 text-xs text-[var(--color-muted)]">
            {crumbs.map((c, idx) => (
              <li key={`${c.label}-${idx}`} className="flex items-center gap-1">
                {idx > 0 ? <span aria-hidden="true">/</span> : null}
                {c.to ? (
                  <Link className="rounded hover:text-[var(--color-brand)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-brand)]" to={c.to}>
                    {c.label}
                  </Link>
                ) : (
                  <span aria-current="page" className="font-medium text-[var(--color-ink)]">
                    {c.label}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-[var(--color-ink)] sm:text-4xl">
            {title}
          </h1>
          {subtitle ? <p className="mt-2 max-w-2xl text-[var(--color-muted)]">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
    </header>
  )
}

export function Panel({
  children,
  className = '',
  title,
  action,
}: PropsWithChildren<{ className?: string; title?: string; action?: ReactNode }>) {
  return (
    <section
      className={`animate-rise rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/90 p-5 shadow-[0_10px_30px_rgba(11,31,42,0.04)] ${className}`}
    >
      {title ? (
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-[var(--color-ink)]">{title}</h2>
          {action}
        </div>
      ) : null}
      {children}
    </section>
  )
}

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }) {
  const styles =
    variant === 'primary'
      ? 'bg-[var(--color-brand)] text-white hover:bg-[var(--color-brand-dark)]'
      : variant === 'danger'
        ? 'bg-[var(--color-danger)] text-white hover:opacity-90'
        : 'border border-[var(--color-line)] bg-white text-[var(--color-ink)] hover:bg-[var(--color-surface)]'
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand)] disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`}
      {...props}
    />
  )
}

export function Input({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--color-brand)] ${className}`}
      {...props}
    />
  )
}

export function Select({
  className = '',
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--color-brand)] ${className}`}
      {...props}
    >
      {children}
    </select>
  )
}

export function Label({ children, htmlFor }: PropsWithChildren<{ htmlFor?: string }>) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-[var(--color-ink)]">
      {children}
    </label>
  )
}

export function FieldError({ message }: { message?: string }) {
  if (!message) return null
  return (
    <p role="alert" className="mt-1 text-xs text-[var(--color-danger)]">
      {message}
    </p>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'cancelled' || status === 'no_show' || status === 'rejected'
      ? 'bg-red-50 text-red-700'
      : status === 'completed'
        ? 'bg-emerald-50 text-emerald-700'
        : status === 'confirmed'
          ? 'bg-teal-50 text-teal-800'
          : status === 'pending'
            ? 'bg-amber-50 text-amber-800'
            : 'bg-slate-100 text-slate-700'
  return <span className={`rounded-md px-2 py-1 text-xs font-semibold capitalize ${tone}`}>{status}</span>
}

export function EmptyState({
  message,
  action,
}: {
  message: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
      <p className="text-sm text-[var(--color-muted)]">{message}</p>
      {action}
    </div>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10" role="status" aria-live="polite">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-brand-soft)] border-t-[var(--color-brand)]" />
      <span className="text-sm text-[var(--color-muted)]">{label}…</span>
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-[var(--color-brand-soft)]/70 ${className}`} aria-hidden="true" />
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-5 text-center" role="alert">
      <p className="text-sm text-red-700">{message}</p>
      {onRetry ? (
        <Button type="button" variant="secondary" className="mt-3" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  )
}

export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Panel className="!p-4">
      <p className="text-xs uppercase tracking-[0.14em] text-[var(--color-muted)]">{label}</p>
      <p className="mt-2 text-3xl font-bold text-[var(--color-ink)]">{value}</p>
    </Panel>
  )
}
