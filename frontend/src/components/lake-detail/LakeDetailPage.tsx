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

      <ConditionsBanner conditions={detail.conditions} />

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">7-Day Forecast</h2>
        <WeatherTable daily={detail.weather.daily} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">
          Water Level{detail.conditions.water_level_history.length > 0
            ? ` — Last ${Math.round((Date.now() - new Date(detail.conditions.water_level_history[0].timestamp).getTime()) / 86400000)} Days`
            : ''}
        </h2>
        <WaterLevelChart
          history={detail.conditions.water_level_history}
          unit={detail.conditions.water_level_ft !== null ? 'ft' : '%'}
        />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Water Temperature — Last 90 Days</h2>
        <WaterTempChart history={detail.conditions.water_temp_history} />
      </section>
    </div>
  )
}
