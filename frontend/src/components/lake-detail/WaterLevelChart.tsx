import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import type { HistoricalPoint } from '../../api/types'

interface Props {
  history: HistoricalPoint[]
  unitLabel?: string
  fullPoolFt?: number
  deadPoolFt?: number
  emptyMessage?: string
}

const YEAR_COLORS = ['#0284c7', '#16a34a', '#dc2626', '#d97706', '#7c3aed', '#db2777']

const MONTH_TICKS = ['01-01', '02-01', '03-01', '04-01', '05-01', '06-01',
                     '07-01', '08-01', '09-01', '10-01', '11-01', '12-01']
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_TICK_LABELS: Record<string, string> = Object.fromEntries(
  MONTH_TICKS.map((t, i) => [t, MONTH_NAMES[i]])
)

function toMMDD(ts: string): string {
  const d = new Date(ts)
  const m = String(d.getUTCMonth() + 1).padStart(2, '0')
  const day = String(d.getUTCDate()).padStart(2, '0')
  return `${m}-${day}`
}

function formatDateLabel(mmdd: string): string {
  const [m, d] = mmdd.split('-')
  return `${MONTH_NAMES[parseInt(m) - 1]} ${parseInt(d)}`
}

export function WaterLevelChart({
  history,
  unitLabel = 'ft above sea level',
  fullPoolFt,
  deadPoolFt,
  emptyMessage = 'No water level data available',
}: Props) {
  const canShowPct = fullPoolFt !== undefined && deadPoolFt !== undefined
  const [displayMode, setDisplayMode] = useState<'elevation' | 'pct'>('elevation')
  const [showFullPool, setShowFullPool] = useState(false)
  const [showDeadPool, setShowDeadPool] = useState(false)

  const byYear = useMemo(() => {
    const map: Record<number, Record<string, number>> = {}
    for (const pt of history) {
      const d = new Date(pt.timestamp)
      const year = d.getUTCFullYear()
      const key = toMMDD(pt.timestamp)
      if (!map[year]) map[year] = {}
      map[year][key] = pt.value
    }
    return map
  }, [history])

  const allYears = useMemo(
    () => Object.keys(byYear).map(Number).sort((a, b) => b - a),
    [byYear]
  )

  const currentYear = new Date().getFullYear()

  const [selectedYears, setSelectedYears] = useState<Set<number>>(() => {
    const initial = new Set<number>()
    if (allYears.includes(currentYear)) initial.add(currentYear)
    if (allYears.includes(currentYear - 1)) initial.add(currentYear - 1)
    if (initial.size === 0 && allYears[0] !== undefined) initial.add(allYears[0])
    return initial
  })

  const toPct = (v: number) =>
    ((v - deadPoolFt!) / (fullPoolFt! - deadPoolFt!)) * 100

  const chartData = useMemo(() => {
    const allKeys = new Set<string>()
    for (const year of allYears) {
      for (const key of Object.keys(byYear[year] ?? {})) {
        allKeys.add(key)
      }
    }
    const sortedKeys = Array.from(allKeys).sort()
    return sortedKeys.map(key => {
      const row: Record<string, string | number> = { mmdd: key }
      for (const year of allYears) {
        const raw = byYear[year]?.[key]
        if (raw !== undefined) {
          row[String(year)] = displayMode === 'pct' && canShowPct ? toPct(raw) : raw
        }
      }
      return row
    })
  }, [byYear, allYears, displayMode, canShowPct])

  const yearColorMap = useMemo(
    () => Object.fromEntries(allYears.map((y, i) => [y, YEAR_COLORS[i % YEAR_COLORS.length]])),
    [allYears]
  )

  const yDomain = useMemo(() => {
    let min = Infinity
    let max = -Infinity
    for (const row of chartData) {
      for (const year of allYears) {
        const v = row[String(year)] as number | undefined
        if (v !== undefined) {
          if (v < min) min = v
          if (v > max) max = v
        }
      }
    }
    if (showFullPool && fullPoolFt !== undefined) {
      const ref = displayMode === 'pct' ? 100 : fullPoolFt
      if (ref < min) min = ref
      if (ref > max) max = ref
    }
    if (showDeadPool && deadPoolFt !== undefined) {
      const ref = displayMode === 'pct' ? 0 : deadPoolFt
      if (ref < min) min = ref
      if (ref > max) max = ref
    }
    if (!isFinite(min) || !isFinite(max)) return ['auto', 'auto'] as ['auto', 'auto']
    const pad = (max - min) * 0.04
    return [min - pad, max + pad] as [number, number]
  }, [chartData, allYears, showFullPool, showDeadPool, fullPoolFt, deadPoolFt, displayMode])

  const toggleYear = (year: number) => {
    setSelectedYears(prev => {
      const next = new Set(prev)
      if (next.has(year)) {
        if (next.size > 1) next.delete(year)
      } else {
        next.add(year)
      }
      return next
    })
  }

  if (history.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg text-gray-400 text-sm">
        {emptyMessage}
      </div>
    )
  }

  const activeUnitLabel = displayMode === 'pct' ? '% full' : unitLabel

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex flex-wrap gap-2">
          {allYears.map(year => {
            const color = yearColorMap[year]
            const active = selectedYears.has(year)
            return (
              <button
                key={year}
                onClick={() => toggleYear(year)}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  active ? 'text-white border-transparent' : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-50'
                }`}
                style={active ? { backgroundColor: color, borderColor: color } : {}}
              >
                {year}
              </button>
            )
          })}
          {fullPoolFt !== undefined && (
            <button
              onClick={() => setShowFullPool(v => !v)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                showFullPool ? 'bg-emerald-600 text-white border-transparent' : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Full Pool
            </button>
          )}
          {deadPoolFt !== undefined && (
            <button
              onClick={() => setShowDeadPool(v => !v)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                showDeadPool ? 'bg-red-500 text-white border-transparent' : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Dead Pool
            </button>
          )}
        </div>
        {canShowPct && (
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
            <button
              onClick={() => setDisplayMode('elevation')}
              className={`px-3 py-1 ${displayMode === 'elevation' ? 'bg-ocean-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              Elevation
            </button>
            <button
              onClick={() => setDisplayMode('pct')}
              className={`px-3 py-1 border-l border-gray-200 ${displayMode === 'pct' ? 'bg-ocean-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              % Full
            </button>
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="mmdd"
            ticks={MONTH_TICKS}
            tickFormatter={(v: string) => MONTH_TICK_LABELS[v] ?? ''}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            domain={yDomain}
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => displayMode === 'pct' ? `${v.toFixed(0)}%` : v.toFixed(0)}
            label={{ value: activeUnitLabel, angle: -90, position: 'insideLeft', offset: -4, style: { fontSize: 10, fill: '#6b7280' } }}
            width={56}
          />
          <Tooltip
            labelFormatter={(label: string) => formatDateLabel(label)}
            formatter={(value: number, name: string) => [
              displayMode === 'pct' ? `${value.toFixed(1)}%` : `${value.toFixed(1)} ft`,
              name,
            ]}
          />
          {showFullPool && fullPoolFt !== undefined && (
            <ReferenceLine
              y={displayMode === 'pct' ? 100 : fullPoolFt}
              stroke="#059669"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              label={{ value: 'Full Pool', position: 'insideTopRight', fontSize: 10, fill: '#059669' }}
            />
          )}
          {showDeadPool && deadPoolFt !== undefined && (
            <ReferenceLine
              y={displayMode === 'pct' ? 0 : deadPoolFt}
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              label={{ value: 'Dead Pool', position: 'insideBottomRight', fontSize: 10, fill: '#ef4444' }}
            />
          )}
          {allYears
            .filter(year => selectedYears.has(year))
            .map(year => (
              <Line
                key={year}
                type="monotone"
                dataKey={String(year)}
                stroke={yearColorMap[year]}
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
            ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
