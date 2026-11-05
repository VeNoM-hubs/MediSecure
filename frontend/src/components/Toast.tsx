import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

type ToastKind = 'success' | 'error' | 'info'

interface ToastItem {
  id: number
  message: string
  kind: ToastKind
}

interface ToastContextValue {
  push: (message: string, kind?: ToastKind) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const push = useCallback((message: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.floor(Math.random() * 1000)
    setItems((prev) => [...prev, { id, message, kind }])
    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id))
    }, 3500)
  }, [])

  const value = useMemo(() => ({ push }), [push])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={`animate-rise rounded-lg px-4 py-3 text-sm text-white shadow-lg ${
              t.kind === 'success' ? 'bg-[var(--color-ok)]' : t.kind === 'error' ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-brand)]'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
