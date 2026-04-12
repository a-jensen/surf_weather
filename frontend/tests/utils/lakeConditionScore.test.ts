import { describe, it, expect } from 'vitest'
import { getLakeConditionScore, ConditionScore } from '../../src/utils/lakeConditionScore'
import type { DailyForecast } from '../../src/api/types'

function makeDay(overrides: Partial<DailyForecast> = {}): DailyForecast {
  return {
    date: '2024-06-01',
    temp_high_f: 82,
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

describe('getLakeConditionScore', () => {
  it('returns Good for ideal conditions', () => {
    const score = getLakeConditionScore(makeDay())
    expect(score).toBe(ConditionScore.Good)
  })

  it('returns Poor when thunderstorm risk is true', () => {
    const score = getLakeConditionScore(makeDay({ has_thunderstorm_risk: true }))
    expect(score).toBe(ConditionScore.Poor)
  })

  it('returns Poor when rain chance is high', () => {
    const score = getLakeConditionScore(makeDay({ precip_probability_pct: 75 }))
    expect(score).toBe(ConditionScore.Poor)
  })

  it('returns Fair when wind speed is moderate', () => {
    const score = getLakeConditionScore(makeDay({ wind_speed_mph: 18 }))
    expect(score).toBe(ConditionScore.Fair)
  })

  it('returns Poor when wind speed is high', () => {
    const score = getLakeConditionScore(makeDay({ wind_speed_mph: 28 }))
    expect(score).toBe(ConditionScore.Poor)
  })

  it('returns Fair when rain chance is moderate', () => {
    const score = getLakeConditionScore(makeDay({ precip_probability_pct: 40 }))
    expect(score).toBe(ConditionScore.Fair)
  })

  it('returns a score label string', () => {
    const score = getLakeConditionScore(makeDay())
    expect(['Good', 'Fair', 'Poor']).toContain(score)
  })

  it('thunderstorm overrides other factors', () => {
    // Even perfect conditions should be Poor if there is a thunderstorm
    const score = getLakeConditionScore(
      makeDay({ has_thunderstorm_risk: true, wind_speed_mph: 5, precip_probability_pct: 0 })
    )
    expect(score).toBe(ConditionScore.Poor)
  })
})

describe('getLakeConditionScore — threshold boundaries', () => {
  // Wind boundaries
  it('returns Good at wind 14 mph (just below Fair threshold)', () => {
    expect(getLakeConditionScore(makeDay({ wind_speed_mph: 14 }))).toBe(ConditionScore.Good)
  })

  it('returns Fair at wind 15 mph (Fair threshold)', () => {
    expect(getLakeConditionScore(makeDay({ wind_speed_mph: 15 }))).toBe(ConditionScore.Fair)
  })

  it('returns Fair at wind 21 mph (just below Poor threshold)', () => {
    expect(getLakeConditionScore(makeDay({ wind_speed_mph: 21 }))).toBe(ConditionScore.Fair)
  })

  it('returns Poor at wind 22 mph (Poor threshold)', () => {
    expect(getLakeConditionScore(makeDay({ wind_speed_mph: 22 }))).toBe(ConditionScore.Poor)
  })

  // Rain boundaries
  it('returns Good at rain 29% (just below Fair threshold)', () => {
    expect(getLakeConditionScore(makeDay({ precip_probability_pct: 29 }))).toBe(ConditionScore.Good)
  })

  it('returns Fair at rain 30% (Fair threshold)', () => {
    expect(getLakeConditionScore(makeDay({ precip_probability_pct: 30 }))).toBe(ConditionScore.Fair)
  })

  it('returns Fair at rain 59% (just below Poor threshold)', () => {
    expect(getLakeConditionScore(makeDay({ precip_probability_pct: 59 }))).toBe(ConditionScore.Fair)
  })

  it('returns Poor at rain 60% (Poor threshold)', () => {
    expect(getLakeConditionScore(makeDay({ precip_probability_pct: 60 }))).toBe(ConditionScore.Poor)
  })
})
