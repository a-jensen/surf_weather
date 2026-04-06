import { describe, it, expect } from 'vitest'
import { formatTemp, formatWind, formatDate, formatWaterTemp, celsiusToFahrenheit } from '../../src/utils/formatters'

describe('formatTemp', () => {
  it('formats a temperature with degree symbol', () => {
    expect(formatTemp(85)).toBe('85°F')
  })

  it('rounds to integer', () => {
    expect(formatTemp(84.7)).toBe('85°F')
  })
})

describe('formatWind', () => {
  it('formats wind speed in mph', () => {
    expect(formatWind(12)).toBe('12 mph')
  })

  it('rounds to integer', () => {
    expect(formatWind(12.4)).toBe('12 mph')
  })
})

describe('formatDate', () => {
  it('formats an ISO date string to short form', () => {
    const result = formatDate('2024-06-01')
    expect(result).toContain('Jun')
    expect(result).toContain('1')
  })
})

describe('formatWaterTemp', () => {
  it('formats celsius to fahrenheit display', () => {
    const result = formatWaterTemp(20)
    expect(result).toContain('°F')
  })

  it('returns N/A for null', () => {
    expect(formatWaterTemp(null)).toBe('N/A')
  })
})

describe('celsiusToFahrenheit', () => {
  it('converts 0°C to 32°F', () => {
    expect(celsiusToFahrenheit(0)).toBe(32)
  })

  it('converts 100°C to 212°F', () => {
    expect(celsiusToFahrenheit(100)).toBe(212)
  })

  it('converts 20°C to 68°F', () => {
    expect(celsiusToFahrenheit(20)).toBe(68)
  })
})
