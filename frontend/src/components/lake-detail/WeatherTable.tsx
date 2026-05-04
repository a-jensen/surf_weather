import { useState } from 'react'
import type { DailyForecast, HourlyForecast } from '../../api/types'
import { WeatherIcon } from '../shared/WeatherIcon'
import { WindIndicator } from '../shared/WindIndicator'
import { formatDate, formatTemp } from '../../utils/formatters'
import { getLakeConditionScore, SCORE_COLORS } from '../../utils/lakeConditionScore'
import { getWeatherLabel } from '../../utils/weatherCodes'

interface Props {
  daily: DailyForecast[]
  hourly: HourlyForecast[]
}

function formatHourlyTime(isoTime: string): string {
  // isoTime format: "2024-06-01T14:00"
  const [datePart, timePart] = isoTime.split('T')
  const [year, month, day] = datePart.split('-').map(Number)
  const [hour, minute] = timePart.split(':').map(Number)
  const d = new Date(year, month - 1, day, hour, minute)
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
}

export function WeatherTable({ daily, hourly }: Props) {
  const [expandedDate, setExpandedDate] = useState<string | null>(null)

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
            const isExpanded = expandedDate === day.date
            const dayHourly = hourly.filter((h) => h.iso_time.slice(0, 10) === day.date)

            return (
              <>
                <tr
                  key={day.date}
                  className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer select-none"
                  onClick={() => setExpandedDate(isExpanded ? null : day.date)}
                >
                  <td className="py-2 pr-4 font-medium">
                    <span className="inline-block w-4 text-gray-400 text-xs mr-1">
                      {isExpanded ? '▾' : '▸'}
                    </span>
                    {formatDate(day.date)}
                  </td>
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

                {isExpanded && dayHourly.length > 0 && (
                  <tr key={`${day.date}-hourly`} className="bg-gray-50 border-b border-gray-100">
                    <td colSpan={7} className="px-6 py-2">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr className="text-gray-400 border-b border-gray-200">
                            <th className="pb-1 pr-4 text-left font-normal">Time</th>
                            <th className="pb-1 pr-4 text-left font-normal">Conditions</th>
                            <th className="pb-1 pr-4 text-left font-normal">Temp</th>
                            <th className="pb-1 pr-4 text-left font-normal">Wind</th>
                            <th className="pb-1 text-left font-normal">Rain %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dayHourly.map((h) => (
                            <tr key={h.iso_time} className="border-b border-gray-100 last:border-0">
                              <td className="py-1 pr-4 text-gray-500">{formatHourlyTime(h.iso_time)}</td>
                              <td className="py-1 pr-4">
                                <div className="flex items-center gap-1">
                                  <WeatherIcon code={h.weather_code} className="text-sm" />
                                  <span className="text-gray-600">{getWeatherLabel(h.weather_code)}</span>
                                </div>
                              </td>
                              <td className="py-1 pr-4">{formatTemp(h.temp_f)}</td>
                              <td className="py-1 pr-4">
                                <WindIndicator speedMph={h.wind_speed_mph} directionDeg={h.wind_direction_deg} />
                              </td>
                              <td className="py-1">{Math.round(h.precip_probability_pct)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
