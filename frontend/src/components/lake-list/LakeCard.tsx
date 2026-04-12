import { useNavigate } from 'react-router-dom'
import type { LakeSummary } from '../../api/types'
import { DayBadge } from './DayBadge'
import { formatWaterTemp, formatWaterLevel } from '../../utils/formatters'

interface Props {
  lake: LakeSummary
  isPinned?: boolean
  onTogglePin?: (lakeId: string) => void
}

function PinFilledIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M16 9V4h1a1 1 0 000-2H7a1 1 0 000 2h1v5l-2 3v2h5v5l1 1 1-1v-5h5v-2l-2-3z" />
    </svg>
  )
}

function PinOutlineIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V4.5h.75a.75.75 0 000-1.5h-9a.75.75 0 000 1.5h.75V9l-1.5 3v1.5h4.5V19.5l.75.75.75-.75V13.5h4.5V12l-1.5-3z" />
    </svg>
  )
}

export function LakeCard({ lake, isPinned = false, onTogglePin }: Props) {
  const navigate = useNavigate()

  return (
    <div
      className="bg-white rounded-xl shadow hover:shadow-md transition-shadow cursor-pointer border border-gray-100"
      onClick={() => navigate(`/lakes/${lake.lake_id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/lakes/${lake.lake_id}`)}
      aria-label={`View details for ${lake.name}`}
    >
      <div className="p-4 border-b border-gray-100">
        <div className="flex justify-between items-start">
          <div className="flex items-start gap-2">
            {onTogglePin && (
              <button
                onClick={(e) => { e.stopPropagation(); onTogglePin(lake.lake_id) }}
                onKeyDown={(e) => e.stopPropagation()}
                aria-label={isPinned ? `Unpin ${lake.name}` : `Pin ${lake.name}`}
                className="mt-1 flex-shrink-0 text-gray-300 hover:text-blue-500 transition-colors"
              >
                {isPinned
                  ? <PinFilledIcon className="w-4 h-4 text-blue-500" />
                  : <PinOutlineIcon className="w-4 h-4" />
                }
              </button>
            )}
            <div>
              <h2 className="text-lg font-bold text-gray-900">{lake.name}</h2>
              <span className="text-sm text-gray-500">{lake.state}</span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-600 space-y-1">
            <div>🌡️ Water: <strong>{formatWaterTemp(lake.current_water_temp_c)}</strong></div>
            <div>📏 Level: <strong>{formatWaterLevel(lake.current_water_level_ft, lake.current_water_level_pct)}</strong></div>
          </div>
        </div>
      </div>
      <div className="p-4">
        {lake.forecast.length > 0
          ? <div className="grid grid-cols-4 sm:grid-cols-7 gap-1">{lake.forecast.map((day) => <DayBadge key={day.date} day={day} />)}</div>
          : <p className="text-center text-xs text-gray-400 py-1">Forecast unavailable</p>
        }
      </div>
    </div>
  )
}
