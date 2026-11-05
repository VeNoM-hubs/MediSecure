import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      role: 'patient',
      full_name: 'Jordan Lee',
      user_id: '1',
      access_token: 't',
    },
  }),
}))

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(async (url: string) => {
      if (url === '/appointments') {
        return {
          data: {
            items: [
              {
                id: 'a1',
                patient_id: 'p1',
                doctor_id: 'd1',
                scheduled_at: new Date(Date.now() + 86400000).toISOString(),
                status: 'confirmed',
                doctor_name: 'Dr. Rivera',
              },
            ],
          },
        }
      }
      if (url === '/notifications') return { data: [] }
      if (url === '/notifications/unread-count') return { data: { unread_count: 2 } }
      if (url === '/doctors') {
        return {
          data: [{ id: 'd1', full_name: 'Dr. Rivera', specialization_name: 'GP', years_experience: 5, is_active: true, user_id: 'u', email: 'd@example.com' }],
        }
      }
      if (url === '/medical-records/mine') return { data: [] }
      return { data: {} }
    }),
  },
  getErrorMessage: (e: unknown) => String(e),
}))

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders patient overview with quick actions and stats', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText(/Welcome, Jordan/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: /Book appointment/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /View records/i })).toBeInTheDocument()
    expect(screen.getByText('Unread alerts')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getAllByText('Dr. Rivera').length).toBeGreaterThan(0)
  })
})
