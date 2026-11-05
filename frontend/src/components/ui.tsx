import type { ButtonHTMLAttributes, InputHTMLAttributes, PropsWithChildren } from 'react'

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="mb-8 animate-rise">
      <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight text-[var(--color-ink)] sm:text-4xl">
        {title}
      </h1>
      {subtitle ? <p className="mt-2 max-w-2xl text-[var(--color-muted)]">{subtitle}</p> : null}
    </header>
  )
}

export function Panel({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return (
    <section
      className={`animate-rise rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/90 p-5 shadow-[0_10px_30px_rgba(11,31,42,0.04)] ${className}`}
    >
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
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`}
      {...props}
    />
  )
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className="w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2.5 text-sm outline-none ring-[var(--color-brand)] transition focus:ring-2"
      {...props}
    />
  )
}

export function Label({ children }: PropsWithChildren) {
  return <label className="mb-1.5 block text-sm font-medium text-[var(--color-ink)]">{children}</label>
}

export function FieldError({ message }: { message?: string }) {
  if (!message) return null
  return <p className="mt-1 text-xs text-[var(--color-danger)]">{message}</p>
}

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'cancelled' || status === 'no_show'
      ? 'bg-red-50 text-red-700'
      : status === 'completed'
        ? 'bg-emerald-50 text-emerald-700'
        : status === 'confirmed'
          ? 'bg-teal-50 text-teal-800'
          : 'bg-slate-100 text-slate-700'
  return <span className={`rounded-md px-2 py-1 text-xs font-semibold capitalize ${tone}`}>{status}</span>
}

export function EmptyState({ message }: { message: string }) {
  return <p className="py-8 text-center text-sm text-[var(--color-muted)]">{message}</p>
}
