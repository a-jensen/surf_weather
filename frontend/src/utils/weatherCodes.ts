const THUNDERSTORM_CODES = new Set([95, 96, 99])

interface WeatherInfo {
  label: string
  icon: string
}

const WMO_MAP: Record<number, WeatherInfo> = {
  0:  { label: 'Clear',              icon: '☀️'  },
  1:  { label: 'Mainly Clear',       icon: '🌤️'  },
  2:  { label: 'Partly Cloudy',      icon: '⛅'  },
  3:  { label: 'Overcast',           icon: '☁️'  },
  45: { label: 'Foggy',              icon: '🌫️'  },
  48: { label: 'Icy Fog',            icon: '🌫️'  },
  51: { label: 'Light Drizzle',      icon: '🌦️'  },
  53: { label: 'Drizzle',            icon: '🌦️'  },
  55: { label: 'Heavy Drizzle',      icon: '🌧️'  },
  61: { label: 'Light Rain',         icon: '🌧️'  },
  63: { label: 'Rain',               icon: '🌧️'  },
  65: { label: 'Heavy Rain',         icon: '🌧️'  },
  71: { label: 'Light Snow',         icon: '🌨️'  },
  73: { label: 'Snow',               icon: '❄️'  },
  75: { label: 'Heavy Snow',         icon: '❄️'  },
  77: { label: 'Snow Grains',        icon: '🌨️'  },
  80: { label: 'Light Showers',      icon: '🌦️'  },
  81: { label: 'Showers',            icon: '🌧️'  },
  82: { label: 'Heavy Showers',      icon: '⛈️'  },
  85: { label: 'Snow Showers',       icon: '🌨️'  },
  86: { label: 'Heavy Snow Showers', icon: '❄️'  },
  95: { label: 'Thunderstorm',       icon: '⛈️'  },
  96: { label: 'Thunderstorm + Hail',icon: '⛈️'  },
  99: { label: 'Thunderstorm + Heavy Hail', icon: '⛈️' },
}

const FALLBACK: WeatherInfo = { label: 'Unknown', icon: '❓' }

export function getWeatherInfo(code: number): WeatherInfo {
  return WMO_MAP[code] ?? FALLBACK
}

export function getWeatherLabel(code: number): string {
  return getWeatherInfo(code).label
}

export function getWeatherIcon(code: number): string {
  return getWeatherInfo(code).icon
}

export function isThunderstorm(code: number): boolean {
  return THUNDERSTORM_CODES.has(code)
}
