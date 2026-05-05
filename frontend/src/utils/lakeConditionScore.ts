import type { DailyForecast, HourlyForecast } from '../api/types'

export type ConditionScoreValue = 'Good' | 'Fair' | 'Poor'

export const ConditionScore = {
  Good: 'Good' as const,
  Fair: 'Fair' as const,
  Poor: 'Poor' as const,
}

const WIND_FAIR_THRESHOLD = 15   // mph
const WIND_POOR_THRESHOLD = 22   // mph
const RAIN_FAIR_THRESHOLD = 30   // %
const RAIN_POOR_THRESHOLD = 60   // %
const CAPE_LIGHTNING_THRESHOLD_JKG = 500

export function getLakeConditionScore(day: DailyForecast): ConditionScoreValue {
  if (day.has_thunderstorm_risk) return ConditionScore.Poor
  if (day.wind_speed_mph >= WIND_POOR_THRESHOLD) return ConditionScore.Poor
  if (day.precip_probability_pct >= RAIN_POOR_THRESHOLD) return ConditionScore.Poor
  if (day.wind_speed_mph >= WIND_FAIR_THRESHOLD) return ConditionScore.Fair
  if (day.precip_probability_pct >= RAIN_FAIR_THRESHOLD) return ConditionScore.Fair
  return ConditionScore.Good
}

export function getHourlyConditionScore(h: HourlyForecast): ConditionScoreValue {
  const hasThunderstormRisk = h.cape_jkg > CAPE_LIGHTNING_THRESHOLD_JKG
  if (hasThunderstormRisk) return ConditionScore.Poor
  if (h.wind_speed_mph >= WIND_POOR_THRESHOLD) return ConditionScore.Poor
  if (h.precip_probability_pct >= RAIN_POOR_THRESHOLD) return ConditionScore.Poor
  if (h.wind_speed_mph >= WIND_FAIR_THRESHOLD) return ConditionScore.Fair
  if (h.precip_probability_pct >= RAIN_FAIR_THRESHOLD) return ConditionScore.Fair
  return ConditionScore.Good
}

export const SCORE_COLORS: Record<ConditionScoreValue, string> = {
  Good: 'bg-green-100 text-green-800',
  Fair: 'bg-yellow-100 text-yellow-800',
  Poor: 'bg-red-100 text-red-800',
}

export const SCORE_ROW_COLORS: Record<ConditionScoreValue, string> = {
  Good: 'bg-green-50 hover:bg-green-100',
  Fair: 'bg-yellow-50 hover:bg-yellow-100',
  Poor: 'bg-red-50 hover:bg-red-100',
}

export const SCORE_ROW_BG: Record<ConditionScoreValue, string> = {
  Good: 'bg-green-50',
  Fair: 'bg-yellow-50',
  Poor: 'bg-red-50',
}
