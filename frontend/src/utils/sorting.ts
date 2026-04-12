import type { LakeSummary } from '../api/types'
import { getLakeConditionScore } from './lakeConditionScore'
import { haversineDistanceMiles } from './distance'

export type SortOption = 'default' | 'name' | 'temperature' | 'conditions' | 'distance'

const SCORE_ORDER = { Good: 0, Fair: 1, Poor: 2 } as const

export function sortLakes(
  lakes: LakeSummary[],
  sortBy: SortOption,
  coords: { lat: number; lng: number } | null,
): LakeSummary[] {
  if (sortBy === 'default') return [...lakes]

  const sorted = [...lakes]

  if (sortBy === 'name') {
    return sorted.sort((a, b) => a.name.localeCompare(b.name))
  }

  if (sortBy === 'temperature') {
    return sorted.sort((a, b) => {
      if (a.current_water_temp_c === null && b.current_water_temp_c === null) return 0
      if (a.current_water_temp_c === null) return 1
      if (b.current_water_temp_c === null) return -1
      return b.current_water_temp_c - a.current_water_temp_c
    })
  }

  if (sortBy === 'conditions') {
    return sorted.sort((a, b) => {
      const scoreA = a.forecast.length > 0 ? SCORE_ORDER[getLakeConditionScore(a.forecast[0])] : 3
      const scoreB = b.forecast.length > 0 ? SCORE_ORDER[getLakeConditionScore(b.forecast[0])] : 3
      return scoreA - scoreB
    })
  }

  if (sortBy === 'distance' && coords) {
    return sorted.sort((a, b) =>
      haversineDistanceMiles(coords.lat, coords.lng, a.latitude, a.longitude) -
      haversineDistanceMiles(coords.lat, coords.lng, b.latitude, b.longitude)
    )
  }

  return sorted
}
