import type { LakeConditions } from '../../api/types'
import { formatWaterTemp, formatWaterLevel } from '../../utils/formatters'

interface Props {
  conditions: LakeConditions
  unitPreference?: 'ft' | 'pct'
}

export function ConditionsBanner({ conditions, unitPreference }: Props) {
  const asOf = conditions.data_as_of
    ? new Date(conditions.data_as_of).toLocaleString()
    : null

  return (
    <div className="grid grid-cols-2 gap-4 bg-ocean-50 rounded-xl p-4">
      <div className="text-center">
        <div className="text-2xl font-bold text-ocean-700">
          {formatWaterTemp(conditions.water_temp_c)}
        </div>
        <div className="text-sm text-gray-500 mt-1">Water Temperature</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-ocean-700">
          {unitPreference === 'ft'
            ? (conditions.water_level_ft !== null ? `${conditions.water_level_ft.toFixed(1)} ft` : 'N/A')
            : unitPreference === 'pct'
            ? (conditions.water_level_pct !== null ? `${conditions.water_level_pct.toFixed(1)}% full` : 'N/A')
            : formatWaterLevel(conditions.water_level_ft, conditions.water_level_pct)}
        </div>
        <div className="text-sm text-gray-500 mt-1">Water Level</div>
      </div>
      {asOf && (
        <div className="col-span-2 text-center text-xs text-gray-400">
          Data as of {asOf} · {conditions.provider_name}
        </div>
      )}
      {!asOf && (
        <div className="col-span-2 text-center text-xs text-gray-400">
          No gauge data available for this lake
        </div>
      )}
    </div>
  )
}
