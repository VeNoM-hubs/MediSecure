import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { PageHeader, StatusBadge, EmptyState, ErrorState } from './ui'

describe('UI primitives', () => {
  it('renders page header with crumbs', () => {
    render(
      <MemoryRouter>
        <PageHeader title="MediSecure" subtitle="Secure portal" crumbs={[{ label: 'Home', to: '/' }, { label: 'Page' }]} />
      </MemoryRouter>,
    )
    expect(screen.getByText('MediSecure')).toBeInTheDocument()
    expect(screen.getByText('Secure portal')).toBeInTheDocument()
    expect(screen.getByLabelText('Breadcrumb')).toBeInTheDocument()
  })

  it('renders status badge', () => {
    render(<StatusBadge status="confirmed" />)
    expect(screen.getByText('confirmed')).toBeInTheDocument()
  })

  it('renders empty and error states', () => {
    render(<EmptyState message="Nothing here" />)
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    render(<ErrorState message="Failed" onRetry={() => undefined} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})
