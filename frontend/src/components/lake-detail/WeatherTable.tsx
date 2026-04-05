import type { DailyForecast } from '../../api/types'
import { WeatherIcon } from '../shared/WeatherIcon'
import { WindIndicator } from '../shared/WindIndicator'
import { formatDate, formatTemp } from '../../utils/formatters'
import { getLakeConditionScore, SCORE_COLORS } from '../../utils/lakeConditionScore'
import { getWeatherLabel } from '../../utils/weatherCodes'

interface Props {
  daily: DailyForecast[]
}

export function WeatherTable({ daily }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500 text-left">
            <th className="pb-2 pr-4">Date</th>
            <th className="pb-2 pr-4">Conditions</th>
            <th className="pb-2 pr-4">High / Low</th>
            <th className="pb-2 pr-4">Wind</th>
            <th className="pb-2 pr-4">Rain %</th>
            <th className="pb-2 pr-4">Lightning</th>
            <th className="pb-2">Score</th>
          </tr>
        </thead>
        <tbody>
          {daily.map((day) => {
            const score = getLakeConditionScore(day)
            return (
              <tr key={day.date} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 pr-4 font-medium">{formatDate(day.date)}</td>
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-2">
                    <WeatherIcon code={day.weather_code} className="text-lg" />
                    <span className="text-xs text-gray-600">{getWeatherLabel(day.weather_code)}</span>
                  </div>
                </td>
                <td className="py-2 pr-4">
                  <span className="font-medium">{formatTemp(day.temp_high_f)}</span>
                  <span className="text-gray-400"> / </span>
                  <span>{formatTemp(day.temp_low_f)}</span>
                </td>
                <td className="py-2 pr-4">
                  <WindIndicator speedMph={day.wind_speed_mph} directionDeg={day.wind_direction_deg} />
                </td>
                <td className="py-2 pr-4">{Math.round(day.precip_probability_pct)}%</td>
                <td className="py-2 pr-4">
                  {day.has_thunderstorm_risk ? (
                    <span title="Thunderstorm risk">⚡ Risk</span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="py-2">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SCORE_COLORS[score]}`}>
                    {score}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
