import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DayBadge } from '../../src/components/lake-list/DayBadge'
import type { DailyForecast } from '../../src/api/types'

function makeDay(overrides: Partial<DailyForecast> = {}): DailyForecast {
  return {
    date: '2024-06-01',
    temp_high_f: 85,
    temp_low_f: 62,
    wind_speed_mph: 8,
    wind_direction_deg: 225,
    precip_probability_pct: 10,
    weather_code: 1,
    cape_max_jkg: 0,
    has_thunderstorm_risk: false,
    ...overrides,
  }
}

describe('DayBadge', () => {
  it('renders the formatted date', () => {
    render(<DayBadge day={makeDay()} />)
    expect(screen.getByText(/Jun/)).toBeTruthy()
  })

  it('renders high and low temperatures', () => {
    render(<DayBadge day={makeDay()} />)
    expect(screen.getByText(/85°F/)).toBeTruthy()
    expect(screen.getByText(/62°F/)).toBeTruthy()
  })

  it('renders precipitation probability', () => {
    render(<DayBadge day={makeDay({ precip_probability_pct: 35 })} />)
    expect(screen.getByText(/35%/)).toBeTruthy()
  })

  it('renders wind speed', () => {
    render(<DayBadge day={makeDay({ wind_speed_mph: 12 })} />)
    expect(screen.getByText(/12 mph/)).toBeTruthy()
  })

  it('shows lightning indicator when thunderstorm risk is true', () => {
    render(<DayBadge day={makeDay({ has_thunderstorm_risk: true })} />)
    expect(screen.getByTitle('Thunderstorm risk')).toBeTruthy()
  })

  it('does not show lightning indicator when no thunderstorm risk', () => {
    render(<DayBadge day={makeDay({ has_thunderstorm_risk: false })} />)
    expect(screen.queryByTitle('Thunderstorm risk')).toBeNull()
  })
})
