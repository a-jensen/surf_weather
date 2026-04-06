import { formatWind, windDegToCompass } from '../../utils/formatters'

interface Props {
  speedMph: number
  directionDeg: number
  className?: string
}

export function WindIndicator({ speedMph, directionDeg, className = '' }: Props) {
  return (
    <span className={`inline-flex items-center gap-1 ${className}`}>
      <span
        className="inline-block text-sm"
        style={{ transform: `rotate(${directionDeg}deg)` }}
        aria-hidden="true"
      >
        ↑
      </span>
      <span>{formatWind(speedMph)}</span>
      <span className="text-xs text-gray-500">{windDegToCompass(directionDeg)}</span>
    </span>
  )
}
