import { describe, it, expect } from 'vitest'
import { getWeatherLabel, getWeatherIcon, isThunderstorm } from '../../src/utils/weatherCodes'

describe('getWeatherLabel', () => {
  it('returns label for clear sky (0)', () => {
    expect(getWeatherLabel(0)).toBe('Clear')
  })

  it('returns label for mainly clear (1)', () => {
    expect(getWeatherLabel(1)).toBe('Mainly Clear')
  })

  it('returns label for partly cloudy (2)', () => {
    expect(getWeatherLabel(2)).toBe('Partly Cloudy')
  })

  it('returns label for overcast (3)', () => {
    expect(getWeatherLabel(3)).toBe('Overcast')
  })

  it('returns label for thunderstorm (95)', () => {
    expect(getWeatherLabel(95)).toBe('Thunderstorm')
  })

  it('returns label for thunderstorm with hail (96)', () => {
    expect(getWeatherLabel(96)).toContain('Thunderstorm')
  })

  it('returns label for heavy thunderstorm (99)', () => {
    expect(getWeatherLabel(99)).toContain('Thunderstorm')
  })

  it('returns Unknown for unrecognized code', () => {
    expect(getWeatherLabel(999)).toBe('Unknown')
  })
})

describe('getWeatherIcon', () => {
  it('returns an emoji for code 0', () => {
    const icon = getWeatherIcon(0)
    expect(typeof icon).toBe('string')
    expect(icon.length).toBeGreaterThan(0)
  })

  it('returns a different icon for thunderstorm vs clear', () => {
    expect(getWeatherIcon(95)).not.toBe(getWeatherIcon(0))
  })

  it('returns a fallback icon for unknown codes', () => {
    const icon = getWeatherIcon(999)
    expect(typeof icon).toBe('string')
    expect(icon.length).toBeGreaterThan(0)
  })
})

describe('isThunderstorm', () => {
  it('returns true for code 95', () => {
    expect(isThunderstorm(95)).toBe(true)
  })

  it('returns true for code 96', () => {
    expect(isThunderstorm(96)).toBe(true)
  })

  it('returns true for code 99', () => {
    expect(isThunderstorm(99)).toBe(true)
  })

  it('returns false for clear sky (0)', () => {
    expect(isThunderstorm(0)).toBe(false)
  })

  it('returns false for rain (61)', () => {
    expect(isThunderstorm(61)).toBe(false)
  })
})
