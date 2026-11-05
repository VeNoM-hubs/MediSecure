import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AppointmentsPage } from './AppointmentsPage'

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: { role: 'patient', full_name: 'Test', user_id: '1', access_token: 't' },
  }),
}))

vi.mock('@/components/Toast', () => ({
  useToast: () => ({ push: vi.fn() }),
}))

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      data: {
        items: [],
        meta: { page: 1, page_size: 50, total: 0, total_pages: 1 },
      },
    }),
  },
  getErrorMessage: (e: unknown) => String(e),
}))

describe('AppointmentsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders filters and empty state', async () => {
    render(
      <MemoryRouter>
        <AppointmentsPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'Appointments' })).toBeInTheDocument()
    expect(screen.getByLabelText('Search')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('No appointments found.')).toBeInTheDocument()
    })
  })
})
