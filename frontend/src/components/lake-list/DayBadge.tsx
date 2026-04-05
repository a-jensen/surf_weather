import type { DailyForecast } from '../../api/types'
import { WeatherIcon } from '../shared/WeatherIcon'
import { formatDate, formatTemp } from '../../utils/formatters'
import { getLakeConditionScore, SCORE_COLORS } from '../../utils/lakeConditionScore'

interface Props {
  day: DailyForecast
}

export function DayBadge({ day }: Props) {
  const score = getLakeConditionScore(day)
  const scoreColor = SCORE_COLORS[score]

  return (
    <div className={`flex flex-col items-center p-2 rounded-lg text-xs ${scoreColor}`}>
      <span className="font-semibold">{formatDate(day.date)}</span>
      <WeatherIcon code={day.weather_code} className="text-xl my-1" />
      <span>{formatTemp(day.temp_high_f)} / {formatTemp(day.temp_low_f)}</span>
      <span className="mt-1">💧 {Math.round(day.precip_probability_pct)}%</span>
      <span>💨 {Math.round(day.wind_speed_mph)} mph</span>
      {day.has_thunderstorm_risk && (
        <span className="mt-1" title="Thunderstorm risk">⚡</span>
      )}
    </div>
  )
}
