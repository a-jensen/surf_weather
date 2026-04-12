import { describe, it, expect } from 'vitest'
import { sortLakes } from '../../src/utils/sorting'
import type { LakeSummary, DailyForecast } from '../../src/api/types'

function makeDay(overrides: Partial<DailyForecast> = {}): DailyForecast {
  return {
    date: '2024-06-01',
    temp_high_f: 80,
    temp_low_f: 60,
    wind_speed_mph: 8,
    wind_direction_deg: 225,
    precip_probability_pct: 5,
    weather_code: 1,
    cape_max_jkg: 0,
    has_thunderstorm_risk: false,
    ...overrides,
  }
}

function makeLake(overrides: Partial<LakeSummary> = {}): LakeSummary {
  return {
    lake_id: 'test_lake',
    name: 'Test Lake',
    state: 'UT',
    latitude: 40.5,
    longitude: -111.5,
    current_water_temp_c: 20,
    current_water_level_ft: 5000,
    current_water_level_pct: 75,
    forecast: [makeDay()],
    weather_error: null,
    ...overrides,
  }
}

const lakeA = makeLake({ lake_id: 'a', name: 'Alpha Lake', current_water_temp_c: 22, latitude: 40.0, longitude: -111.0 })
const lakeB = makeLake({ lake_id: 'b', name: 'Bravo Lake', current_water_temp_c: 18, latitude: 41.0, longitude: -112.0 })
const lakeC = makeLake({ lake_id: 'c', name: 'Charlie Lake', current_water_temp_c: null, latitude: 42.0, longitude: -113.0 })

describe('sortLakes — default', () => {
  it('returns lakes in original order', () => {
    const result = sortLakes([lakeB, lakeA, lakeC], 'default', null)
    expect(result.map(l => l.lake_id)).toEqual(['b', 'a', 'c'])
  })

  it('does not mutate the input array', () => {
    const input = [lakeB, lakeA]
    sortLakes(input, 'default', null)
    expect(input[0].lake_id).toBe('b')
  })
})

describe('sortLakes — name', () => {
  it('sorts alphabetically by name', () => {
    const result = sortLakes([lakeC, lakeA, lakeB], 'name', null)
    expect(result.map(l => l.lake_id)).toEqual(['a', 'b', 'c'])
  })

  it('does not mutate the input array', () => {
    const input = [lakeC, lakeA]
    sortLakes(input, 'name', null)
    expect(input[0].lake_id).toBe('c')
  })
})

describe('sortLakes — temperature', () => {
  it('sorts warmest first', () => {
    const result = sortLakes([lakeC, lakeB, lakeA], 'temperature', null)
    expect(result.map(l => l.lake_id)).toEqual(['a', 'b', 'c'])
  })

  it('places null temperatures at the end', () => {
    const result = sortLakes([lakeC, lakeA], 'temperature', null)
    expect(result[0].lake_id).toBe('a')
    expect(result[1].lake_id).toBe('c')
  })

  it('two nulls remain in stable relative order', () => {
    const lake1 = makeLake({ lake_id: 'x', current_water_temp_c: null })
    const lake2 = makeLake({ lake_id: 'y', current_water_temp_c: null })
    const result = sortLakes([lake1, lake2], 'temperature', null)
    expect(result.map(l => l.lake_id)).toEqual(['x', 'y'])
  })
})

describe('sortLakes — conditions', () => {
  const goodLake = makeLake({ lake_id: 'good', forecast: [makeDay({ wind_speed_mph: 5, precip_probability_pct: 5 })] })
  const fairLake = makeLake({ lake_id: 'fair', forecast: [makeDay({ wind_speed_mph: 18, precip_probability_pct: 5 })] })
  const poorLake = makeLake({ lake_id: 'poor', forecast: [makeDay({ wind_speed_mph: 30, precip_probability_pct: 5 })] })
  const emptyLake = makeLake({ lake_id: 'empty', forecast: [] })

  it('sorts Good before Fair before Poor', () => {
    const result = sortLakes([poorLake, goodLake, fairLake], 'conditions', null)
    expect(result.map(l => l.lake_id)).toEqual(['good', 'fair', 'poor'])
  })

  it('places lakes with no forecast at the end', () => {
    const result = sortLakes([emptyLake, goodLake], 'conditions', null)
    expect(result[0].lake_id).toBe('good')
    expect(result[1].lake_id).toBe('empty')
  })
})

describe('sortLakes — distance', () => {
  const userCoords = { lat: 40.76, lng: -111.89 }

  it('sorts nearest lake first', () => {
    // lakeA is at 40.0, -111.0 and lakeC is at 42.0, -113.0 — lakeA is closer to 40.76, -111.89
    const result = sortLakes([lakeC, lakeA], 'distance', userCoords)
    expect(result[0].lake_id).toBe('a')
  })

  it('falls back to original order when coords is null', () => {
    const result = sortLakes([lakeB, lakeA], 'distance', null)
    expect(result.map(l => l.lake_id)).toEqual(['b', 'a'])
  })
})
