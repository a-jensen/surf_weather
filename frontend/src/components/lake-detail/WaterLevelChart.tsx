import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { HistoricalPoint } from '../../api/types'

interface Props {
  history: HistoricalPoint[]
}

function formatTick(ts: string) {
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function WaterLevelChart({ history }: Props) {
  if (history.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg text-gray-400 text-sm">
        No water level data available
      </div>
    )
  }

  const data = history.map((pt) => ({
    ts: pt.timestamp,
    value: pt.value,
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="ts"
          tickFormatter={formatTick}
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={['auto', 'auto']}
          tick={{ fontSize: 11 }}
          tickFormatter={(v: number) => `${v.toFixed(0)} ft`}
          width={56}
        />
        <Tooltip
          labelFormatter={(label: string) => formatTick(label)}
          formatter={(value: number) => [`${value.toFixed(2)} ft`, 'Level']}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#0284c7"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
