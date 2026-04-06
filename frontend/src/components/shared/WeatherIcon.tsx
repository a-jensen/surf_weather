import { getWeatherIcon, getWeatherLabel } from '../../utils/weatherCodes'

interface Props {
  code: number
  className?: string
}

export function WeatherIcon({ code, className = 'text-2xl' }: Props) {
  return (
    <span className={className} title={getWeatherLabel(code)} aria-label={getWeatherLabel(code)}>
      {getWeatherIcon(code)}
    </span>
  )
}
