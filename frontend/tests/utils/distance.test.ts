import { describe, it, expect } from 'vitest'
import { haversineDistanceMiles } from '../../src/utils/distance'

describe('haversineDistanceMiles', () => {
  it('returns 0 for identical points', () => {
    expect(haversineDistanceMiles(40.0, -111.0, 40.0, -111.0)).toBe(0)
  })

  it('is symmetric', () => {
    const d1 = haversineDistanceMiles(40.7608, -111.8910, 40.2338, -111.6585)
    const d2 = haversineDistanceMiles(40.2338, -111.6585, 40.7608, -111.8910)
    expect(d1).toBeCloseTo(d2, 5)
  })

  it('returns a reasonable distance between Salt Lake City and Provo (~38 mi)', () => {
    const d = haversineDistanceMiles(40.7608, -111.8910, 40.2338, -111.6585)
    expect(d).toBeGreaterThan(35)
    expect(d).toBeLessThan(45)
  })

  it('returns a larger distance for a farther pair of points', () => {
    // User near Salt Lake City
    const userLat = 40.76, userLng = -111.89
    // Willard Bay (~50 mi north) vs Sand Hollow (~300 mi south)
    const dNear = haversineDistanceMiles(userLat, userLng, 41.3867, -112.0825)
    const dFar  = haversineDistanceMiles(userLat, userLng, 37.1147, -113.3913)
    expect(dNear).toBeLessThan(dFar)
  })

  it('returns a positive value for any two distinct points', () => {
    const d = haversineDistanceMiles(40.0, -111.0, 41.0, -112.0)
    expect(d).toBeGreaterThan(0)
  })
})
