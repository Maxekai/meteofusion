import type { AggregatedStat, WeatherCondition } from "../types/weather";

const CONDITION_LABELS: Record<WeatherCondition, string> = {
  sunny: "Soleado",
  partly_cloudy: "Nubes y claros",
  cloudy: "Nublado",
  rain: "Lluvia",
  snow: "Nieve",
  unknown: "Sin clasificar",
};

const PROVIDER_LABELS: Record<string, string> = {
  google_weather: "Google Weather",
  open_meteo: "Open-Meteo",
  weather_api: "WeatherAPI",
};

function dateAtNoon(date: string): Date {
  return new Date(`${date}T12:00:00`);
}

export function conditionLabel(condition: WeatherCondition): string {
  return CONDITION_LABELS[condition] ?? CONDITION_LABELS.unknown;
}

export function providerLabel(provider: string): string {
  return PROVIDER_LABELS[provider] ?? provider.replaceAll("_", " ");
}

export function formatNumber(
  value: number | null,
  maximumFractionDigits = 0,
): string {
  if (value === null || Number.isNaN(value)) {
    return "–";
  }

  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(value);
}

export function formatCoordinate(value: number): string {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDayName(date: string): string {
  return new Intl.DateTimeFormat("es-ES", { weekday: "short" })
    .format(dateAtNoon(date))
    .replace(".", "");
}

export function formatDayMonth(date: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "short",
  })
    .format(dateAtNoon(date))
    .replace(".", "");
}

export function formatLongDate(date: string): string {
  const formatted = new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(dateAtNoon(date));

  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export function formatHour(datetime: string): string {
  return datetime.slice(11, 16);
}

export function statHasSnow(stat: AggregatedStat): boolean {
  return (stat.max ?? 0) > 0;
}
