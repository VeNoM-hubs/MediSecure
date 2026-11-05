import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PageHeader, StatusBadge } from './ui'

describe('UI primitives', () => {
  it('renders page header', () => {
    render(<PageHeader title="MediSecure" subtitle="Secure portal" />)
    expect(screen.getByText('MediSecure')).toBeInTheDocument()
    expect(screen.getByText('Secure portal')).toBeInTheDocument()
  })

  it('renders status badge', () => {
    render(<StatusBadge status="confirmed" />)
    expect(screen.getByText('confirmed')).toBeInTheDocument()
  })
})
