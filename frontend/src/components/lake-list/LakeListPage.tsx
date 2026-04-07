import { useLakes } from '../../hooks/useLakes'
import { LakeCard } from './LakeCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export function LakeListPage() {
  const { lakes, loading, error } = useLakes()

  if (loading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="text-center p-8 text-red-600">
        <p className="text-lg font-semibold">Failed to load lakes</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    )
  }

  const weatherError = lakes.find(l => l.weather_error)?.weather_error ?? null

  return (
    <div className="space-y-4">
      {weatherError && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          {weatherError} — lake conditions are still shown below.
        </div>
      )}
      {lakes.map((lake) => (
        <LakeCard key={lake.lake_id} lake={lake} />
      ))}
    </div>
  )
}
