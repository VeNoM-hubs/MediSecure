import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, beforeEach } from 'vitest'
import { AuthProvider } from '@/context/AuthContext'
import { ProtectedRoute } from './ProtectedRoute'

function renderWithAuth(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<div>Secure dashboard</div>} />
          </Route>
          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="/admin-only" element={<div>Admin area</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects unauthenticated users to login', () => {
    renderWithAuth('/dashboard')
    expect(screen.getByText('Login page')).toBeInTheDocument()
  })

  it('allows authenticated users into protected routes', () => {
    localStorage.setItem(
      'medisecure_auth',
      JSON.stringify({
        access_token: 'token',
        refresh_token: 'refresh',
        user_id: '1',
        full_name: 'Test Patient',
        role: 'patient',
      }),
    )
    renderWithAuth('/dashboard')
    expect(screen.getByText('Secure dashboard')).toBeInTheDocument()
  })

  it('blocks wrong-role access and sends user to dashboard', () => {
    localStorage.setItem(
      'medisecure_auth',
      JSON.stringify({
        access_token: 'token',
        refresh_token: 'refresh',
        user_id: '1',
        full_name: 'Test Patient',
        role: 'patient',
      }),
    )
    renderWithAuth('/admin-only')
    // Role mismatch navigates to /dashboard, which is nested under auth-only outlet
    expect(screen.getByText('Secure dashboard')).toBeInTheDocument()
  })
})
