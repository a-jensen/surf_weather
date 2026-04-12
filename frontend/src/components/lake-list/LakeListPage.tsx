import { useLakes } from '../../hooks/useLakes'
import { useUserLocation } from '../../hooks/useUserLocation'
import { haversineDistanceMiles } from '../../utils/distance'
import { LakeCard } from './LakeCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export function LakeListPage() {
  const { lakes, loading, error } = useLakes()
  const { status, coords, request, clear } = useUserLocation()

  if (loading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="text-center p-8 text-red-600">
        <p className="text-lg font-semibold">Failed to load lakes</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    )
  }

  const sortedLakes =
    status === 'granted' && coords
      ? [...lakes].sort((a, b) =>
          haversineDistanceMiles(coords.lat, coords.lng, a.latitude, a.longitude) -
          haversineDistanceMiles(coords.lat, coords.lng, b.latitude, b.longitude)
        )
      : lakes

  const weatherError = sortedLakes.find(l => l.weather_error)?.weather_error ?? null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {status === 'idle' && (
          <button
            onClick={request}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 7h7m0 0V3m0 4L3 3m18 4h-7m0 0V3m0 4l7-4M3 17h7m0 0v4m0-4L3 21m18-4h-7m0 0v4m0-4l7 4" />
            </svg>
            Sort by distance
          </button>
        )}

        {status === 'loading' && (
          <span className="flex items-center gap-1.5 text-sm text-gray-400">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Getting location…
          </span>
        )}

        {status === 'granted' && (
          <span className="flex items-center gap-2 text-sm text-gray-500">
            <span className="flex items-center gap-1 text-green-700">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Nearest first
            </span>
            <button
              onClick={clear}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Reset sort order"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </span>
        )}

        {status === 'denied' && (
          <span className="flex items-center gap-1.5 text-sm text-gray-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
            </svg>
            Location access denied
          </span>
        )}

        {status === 'unavailable' && (
          <span className="text-sm text-gray-400">Location unavailable</span>
        )}
      </div>

      {weatherError && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          {weatherError} — lake conditions are still shown below.
        </div>
      )}

      {sortedLakes.map((lake) => (
        <LakeCard key={lake.lake_id} lake={lake} />
      ))}
    </div>
  )
}
