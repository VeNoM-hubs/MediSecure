import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { Button } from '@/components/ui'

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=2000&q=80')] bg-cover bg-center"
        aria-hidden
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#0b1f2a]/92 via-[#0b1f2a]/75 to-[#0d7377]/45" />
      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16 text-white">
        <div className="animate-rise max-w-xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm backdrop-blur">
            <Shield className="h-4 w-4" />
            Academic DevSecOps demo
          </div>
          <h1 className="font-[family-name:var(--font-display)] text-5xl font-semibold leading-tight tracking-tight sm:text-6xl">
            MediSecure
          </h1>
          <p className="mt-4 max-w-md text-lg text-white/85">
            A security-first healthcare management portal for patients, doctors, and administrators — built with
            synthetic data only.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/login">
              <Button className="bg-white text-[var(--color-ink)] hover:bg-white/90">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary" className="border-white/40 bg-transparent text-white hover:bg-white/10">
                Patient registration
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
