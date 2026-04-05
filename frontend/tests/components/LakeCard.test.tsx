import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LakeCard } from '../../src/components/lake-list/LakeCard'
import type { LakeSummary, DailyForecast } from '../../src/api/types'

function makeDay(i: number): DailyForecast {
  return {
    date: `2024-06-0${i + 1}`,
    temp_high_f: 80 + i,
    temp_low_f: 60,
    wind_speed_mph: 8,
    wind_direction_deg: 225,
    precip_probability_pct: 5,
    weather_code: 1,
    cape_max_jkg: 0,
    has_thunderstorm_risk: false,
  }
}

function makeLake(overrides: Partial<LakeSummary> = {}): LakeSummary {
  return {
    lake_id: 'deer_creek',
    name: 'Deer Creek Reservoir',
    state: 'UT',
    latitude: 40.4083,
    longitude: -111.5297,
    current_water_temp_c: 18.5,
    current_water_level_ft: 4712.3,
    forecast: Array.from({ length: 7 }, (_, i) => makeDay(i)),
    ...overrides,
  }
}

describe('LakeCard', () => {
  it('renders the lake name', () => {
    render(<MemoryRouter><LakeCard lake={makeLake()} /></MemoryRouter>)
    expect(screen.getByText('Deer Creek Reservoir')).toBeTruthy()
  })

  it('renders the state', () => {
    render(<MemoryRouter><LakeCard lake={makeLake()} /></MemoryRouter>)
    expect(screen.getByText('UT')).toBeTruthy()
  })

  it('renders water temperature', () => {
    render(<MemoryRouter><LakeCard lake={makeLake()} /></MemoryRouter>)
    // 18.5°C → 65°F
    expect(screen.getByText(/65°F/)).toBeTruthy()
  })

  it('renders water level', () => {
    render(<MemoryRouter><LakeCard lake={makeLake()} /></MemoryRouter>)
    expect(screen.getByText(/4712\.3 ft/)).toBeTruthy()
  })

  it('renders N/A for missing water temp', () => {
    render(<MemoryRouter><LakeCard lake={makeLake({ current_water_temp_c: null })} /></MemoryRouter>)
    expect(screen.getByText(/N\/A/)).toBeTruthy()
  })

  it('renders 7 day badges', () => {
    render(<MemoryRouter><LakeCard lake={makeLake()} /></MemoryRouter>)
    // Each day badge has a "Jun" date label
    const junLabels = screen.getAllByText(/Jun/)
    expect(junLabels.length).toBeGreaterThanOrEqual(7)
  })
})
