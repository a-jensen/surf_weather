import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WindIndicator } from '../../src/components/shared/WindIndicator'

describe('WindIndicator', () => {
  it('renders wind speed in mph', () => {
    render(<WindIndicator speedMph={12} directionDeg={270} />)
    expect(screen.getByText('12 mph')).toBeTruthy()
  })

  it('renders compass direction', () => {
    render(<WindIndicator speedMph={10} directionDeg={270} />)
    expect(screen.getByText('W')).toBeTruthy()
  })

  it('renders N for 0 degrees', () => {
    render(<WindIndicator speedMph={5} directionDeg={0} />)
    expect(screen.getByText('N')).toBeTruthy()
  })

  it('renders SW for 225 degrees', () => {
    render(<WindIndicator speedMph={8} directionDeg={225} />)
    expect(screen.getByText('SW')).toBeTruthy()
  })

  it('rounds wind speed', () => {
    render(<WindIndicator speedMph={12.7} directionDeg={0} />)
    expect(screen.getByText('13 mph')).toBeTruthy()
  })
})
