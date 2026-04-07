import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useLakeDetail } from '../../hooks/useLakeDetail'
import { LoadingSpinner } from '../shared/LoadingSpinner'
import { ConditionsBanner } from './ConditionsBanner'
import { WeatherTable } from './WeatherTable'
import { WaterLevelChart } from './WaterLevelChart'
import { WaterTempChart } from './WaterTempChart'

export function LakeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { detail, loading, error } = useLakeDetail(id ?? '')
  const [levelUnit, setLevelUnit] = useState<'ft' | 'pct'>('pct')

  if (loading) return <LoadingSpinner />

  if (error || !detail) {
    return (
      <div className="text-center p-8 text-red-600">
        <p className="text-lg font-semibold">Failed to load lake details</p>
        <p className="text-sm mt-1">{error}</p>
        <button
          className="mt-4 text-ocean-600 underline"
          onClick={() => navigate('/')}
        >
          ← Back to lakes
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-ocean-600 hover:text-ocean-700 text-sm"
        >
          ← All Lakes
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{detail.name}</h1>
        <span className="text-gray-400 text-sm">{detail.state}</span>
      </div>

      <ConditionsBanner conditions={detail.conditions} unitPreference={levelUnit} />

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">7-Day Forecast</h2>
        <WeatherTable daily={detail.weather.daily} />
      </section>

      {(() => {
        const hasBothUnits = detail.conditions.water_level_ft !== null && detail.conditions.water_level_pct !== null
        // History values are elevation ft when water_level_ft is present; pct otherwise
        const historyIsElevation = detail.conditions.water_level_ft !== null
        const chartHistory = levelUnit === 'pct' && historyIsElevation
          ? []
          : detail.conditions.water_level_history
        const chartUnit: 'ft' | '%' = historyIsElevation ? 'ft' : '%'
        const historyDays = detail.conditions.water_level_history.length > 0
          ? Math.round((Date.now() - new Date(detail.conditions.water_level_history[0].timestamp).getTime()) / 86400000)
          : null

        return (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-700">
                Water Level{historyDays !== null ? ` — Last ${historyDays} Days` : ''}
              </h2>
              {hasBothUnits && (
                <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
                  <button
                    onClick={() => setLevelUnit('pct')}
                    className={`px-3 py-1 ${levelUnit === 'pct' ? 'bg-ocean-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                  >
                    % Full
                  </button>
                  <button
                    onClick={() => setLevelUnit('ft')}
                    className={`px-3 py-1 border-l border-gray-200 ${levelUnit === 'ft' ? 'bg-ocean-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                  >
                    Elevation (ft)
                  </button>
                </div>
              )}
            </div>
            <WaterLevelChart
              history={chartHistory}
              unit={chartUnit}
              emptyMessage="Historical % full data is not available for this lake"
            />
          </section>
        )
      })()}


      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Water Temperature — Last 90 Days</h2>
        <WaterTempChart history={detail.conditions.water_temp_history} />
      </section>
    </div>
  )
}
