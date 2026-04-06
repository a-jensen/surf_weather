export function celsiusToFahrenheit(c: number): number {
  return Math.round(c * 9 / 5 + 32)
}

export function formatTemp(f: number): string {
  return `${Math.round(f)}°F`
}

export function formatWind(mph: number): string {
  return `${Math.round(mph)} mph`
}

export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatWaterLevel(ft: number | null, pct: number | null = null): string {
  if (ft !== null) return `${ft.toFixed(1)} ft`
  if (pct !== null) return `${pct.toFixed(1)}% full`
  return 'N/A'
}

export function formatWaterTemp(c: number | null): string {
  if (c === null) return 'N/A'
  return `${celsiusToFahrenheit(c)}°F`
}

export function windDegToCompass(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(deg / 45) % 8]
}
