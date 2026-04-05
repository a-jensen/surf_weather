import { useNavigate } from 'react-router-dom'
import type { LakeSummary } from '../../api/types'
import { DayBadge } from './DayBadge'
import { formatWaterTemp, formatWaterLevel } from '../../utils/formatters'

interface Props {
  lake: LakeSummary
}

export function LakeCard({ lake }: Props) {
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
          <div>
            <h2 className="text-lg font-bold text-gray-900">{lake.name}</h2>
            <span className="text-sm text-gray-500">{lake.state}</span>
          </div>
          <div className="text-right text-sm text-gray-600 space-y-1">
            <div>🌡️ Water: <strong>{formatWaterTemp(lake.current_water_temp_c)}</strong></div>
            <div>📏 Level: <strong>{formatWaterLevel(lake.current_water_level_ft)}</strong></div>
          </div>
        </div>
      </div>
      <div className="p-4 grid grid-cols-7 gap-1">
        {lake.forecast.map((day) => (
          <DayBadge key={day.date} day={day} />
        ))}
      </div>
    </div>
  )
}
