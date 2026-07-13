import type {
  AggregatedForecast,
  LocationCandidate,
  LocationSearchResponse,
} from "../types/weather";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  let message = "No se ha podido completar la peticion.";

  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      message = payload.detail;
    }
  } catch {
    // Keep the generic message when the server does not return JSON.
  }

  throw new ApiError(message, response.status);
}

export async function searchLocations(
  query: string,
  signal?: AbortSignal,
): Promise<LocationSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    count: "10",
    language: "es",
  });
  const response = await fetch(apiUrl(`/api/locations/search?${params}`), {
    signal,
  });

  return parseResponse<LocationSearchResponse>(response);
}

export async function fetchAggregatedForecast(
  location: LocationCandidate,
  signal?: AbortSignal,
): Promise<AggregatedForecast> {
  const response = await fetch(apiUrl("/api/weather/aggregate/forecast"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      location: {
        id: location.id,
        name: location.name,
        display_name: location.display_name,
        latitude: location.latitude,
        longitude: location.longitude,
        timezone: location.timezone,
      },
      days: 7,
    }),
    signal,
  });

  return parseResponse<AggregatedForecast>(response);
}
