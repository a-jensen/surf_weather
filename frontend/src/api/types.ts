export interface DailyForecast {
  date: string
  temp_high_f: number
  temp_low_f: number
  wind_speed_mph: number
  wind_direction_deg: number
  precip_probability_pct: number
  weather_code: number
  cape_max_jkg: number
  has_thunderstorm_risk: boolean
}

export interface HourlyForecast {
  iso_time: string
  temp_f: number
  wind_speed_mph: number
  wind_direction_deg: number
  precip_probability_pct: number
  weather_code: number
  cape_jkg: number
}

export interface WeatherForecast {
  lake_id: string
  timezone: string
  daily: DailyForecast[]
  hourly: HourlyForecast[]
  fetched_at: string
}

export interface HistoricalPoint {
  timestamp: string
  value: number
}

export interface LakeConditions {
  lake_id: string
  water_temp_c: number | null
  water_level_ft: number | null
  water_level_pct: number | null
  water_level_history: HistoricalPoint[]
  water_temp_history: HistoricalPoint[]
  data_as_of: string | null
  provider_name: string
}

export interface LakeSummary {
  lake_id: string
  name: string
  state: string
  latitude: number
  longitude: number
  current_water_temp_c: number | null
  current_water_level_ft: number | null
  current_water_level_pct: number | null
  forecast: DailyForecast[]
  weather_error: string | null
}

export interface LakeDetail {
  lake_id: string
  name: string
  state: string
  latitude: number
  longitude: number
  conditions: LakeConditions
  weather: WeatherForecast
  weather_error: string | null
  lake_level_unit: string | null
  full_pool_elevation_ft: number | null
  dead_pool_elevation_ft: number | null
}
