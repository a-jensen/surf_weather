import { useLakes } from '../../hooks/useLakes'
import { useUserLocation } from '../../hooks/useUserLocation'
import { usePreferences } from '../../hooks/usePreferences'
import { sortLakes } from '../../utils/sorting'
import type { SortOption } from '../../utils/sorting'
import { LakeCard } from './LakeCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

const SORT_LABELS: Record<SortOption, string> = {
  default: 'Default order',
  name: 'Name',
  temperature: 'Warmest water',
  conditions: 'Best conditions',
  distance: 'Nearest first',
}

export function LakeListPage() {
  const { lakes, loading, error } = useLakes()
  const { status, coords, request, clear } = useUserLocation()
  const { pinnedLakes, sortBy, togglePin, setSortBy } = usePreferences()

  if (loading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="text-center p-8 text-red-600">
        <p className="text-lg font-semibold">Failed to load lakes</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    )
  }

  function handleSortChange(newSort: SortOption) {
    if (newSort === 'distance' && sortBy !== 'distance') request()
    if (newSort !== 'distance' && sortBy === 'distance') clear()
    setSortBy(newSort)
  }

  const effectiveCoords = status === 'granted' ? coords : null
  const pinned = sortLakes(lakes.filter(l => pinnedLakes.includes(l.lake_id)), sortBy, effectiveCoords)
  const rest = sortLakes(lakes.filter(l => !pinnedLakes.includes(l.lake_id)), sortBy, effectiveCoords)

  const weatherError = lakes.find(l => l.weather_error)?.weather_error ?? null

  return (
    <div className="space-y-4">
      {/* Controls bar */}
      <div className="flex items-center gap-3">
        <select
          value={sortBy}
          onChange={(e) => handleSortChange(e.target.value as SortOption)}
          className="text-sm text-gray-500 bg-transparent border-none cursor-pointer hover:text-gray-700 transition-colors focus:outline-none"
          aria-label="Sort lakes"
        >
          {(Object.keys(SORT_LABELS) as SortOption[]).map(opt => (
            <option key={opt} value={opt}>{SORT_LABELS[opt]}</option>
          ))}
        </select>

        {sortBy === 'distance' && status === 'loading' && (
          <span className="flex items-center gap-1.5 text-sm text-gray-400">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Getting location…
          </span>
        )}

        {sortBy === 'distance' && status === 'denied' && (
          <span className="flex items-center gap-1.5 text-sm text-gray-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
            </svg>
            Location access denied
          </span>
        )}
      </div>

      {weatherError && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          {weatherError} — lake conditions are still shown below.
        </div>
      )}

      {/* Pinned section */}
      {pinned.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Pinned</h2>
          {pinned.map(lake => (
            <LakeCard key={lake.lake_id} lake={lake} isPinned onTogglePin={togglePin} />
          ))}
        </div>
      )}

      {/* All lakes section */}
      <div className="space-y-4">
        {pinned.length > 0 && (
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">All Lakes</h2>
        )}
        {rest.map(lake => (
          <LakeCard key={lake.lake_id} lake={lake} isPinned={false} onTogglePin={togglePin} />
        ))}
      </div>
    </div>
  )
}
