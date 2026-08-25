export type WeatherCondition =
  | "sunny"
  | "partly_cloudy"
  | "cloudy"
  | "rain"
  | "snow"
  | "unknown";

export interface AggregatedStat {
  min: number | null;
  avg: number | null;
  max: number | null;
}

export interface TemperatureConsensusStat {
  consensus_low: number | null;
  central: number | null;
  consensus_high: number | null;
  provider_min: number | null;
  provider_max: number | null;
  sample_count: number;
}

export interface LocationCandidate {
  id: string;
  provider: string;
  provider_id: number;
  name: string;
  display_name: string;
  latitude: number;
  longitude: number;
  timezone: string;
  country: string | null;
  country_code: string | null;
  admin1: string | null;
  admin2: string | null;
  admin3: string | null;
  admin4: string | null;
  elevation: number | null;
  population: number | null;
}

export interface LocationSearchResponse {
  query: string;
  count: number;
  results: LocationCandidate[];
}

export interface AggregatedHourlyForecastPoint {
  datetime: string;
  provider_count: number;
  temperature_c: TemperatureConsensusStat;
  precipitation_probability: AggregatedStat;
  precipitation_total: AggregatedStat;
  precipitation_snow: AggregatedStat;
  humidity_percent: number | null;
  cloud_cover: number | null;
  wind_speed_kmh: number | null;
  apparent_temperature_c: number | null;
  condition: WeatherCondition;
}

export interface AggregatedDailyForecastPoint {
  date: string;
  provider_count: number;
  temperature_min_c: TemperatureConsensusStat;
  temperature_max_c: TemperatureConsensusStat;
  precipitation_total: AggregatedStat;
  condition: WeatherCondition;
}

export interface AggregatedForecast {
  latitude: number;
  longitude: number;
  timezone: string;
  days: number;
  providers_requested: string[];
  providers_used: string[];
  provider_errors: Record<string, string>;
  warnings: string[];
  hourly_window: {
    mode: string;
    start: string | null;
    end: string | null;
  };
  daily_window: {
    mode: string;
    start: string | null;
    end: string | null;
  };
  hourly_forecast: AggregatedHourlyForecastPoint[];
  daily_forecast: AggregatedDailyForecastPoint[];
}
