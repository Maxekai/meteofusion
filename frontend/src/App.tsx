import { startTransition, useEffect, useRef, useState } from "react";

import { Brand } from "./components/Brand";
import { DailyForecast } from "./components/DailyForecast";
import { HourlyForecast } from "./components/HourlyForecast";
import {
  CalendarIcon,
  DatabaseIcon,
  GlobeIcon,
  InfoIcon,
  MapPinIcon,
} from "./components/Icons";
import { LocationSearch } from "./components/LocationSearch";
import { fetchAggregatedForecast } from "./lib/api";
import { formatCoordinate } from "./lib/format";
import type { AggregatedForecast, LocationCandidate } from "./types/weather";

interface LandingProps {
  loading: boolean;
  error: string | null;
  onLocationSelect: (location: LocationCandidate) => void;
}

function Landing({ loading, error, onLocationSelect }: LandingProps) {
  return (
    <div className="landing-shell">
      <div className="sky-orb sky-orb--one" aria-hidden="true" />
      <div className="sky-orb sky-orb--two" aria-hidden="true" />
      <main className="landing-main">
        <div className="landing-brand">
          <Brand />
        </div>
        <div className="landing-copy">
          <span className="eyebrow">Predicción meteorológica agregada</span>
          <h1>El tiempo, con más de un punto de vista.</h1>
          <p>
            Busca una ubicación y compara el consenso de varios proveedores
            durante los próximos siete días.
          </p>
        </div>

        <LocationSearch
          forecastLoading={loading}
          onSelect={onLocationSelect}
          variant="hero"
        />

        {loading && (
          <div className="forecast-loading" aria-live="polite">
            <span className="forecast-loading-icon" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            <span>
              <strong>Consultando proveedores</strong>
              <small>Estamos cruzando sus predicciones. Puede tardar unos segundos.</small>
            </span>
          </div>
        )}

        {error && !loading && (
          <div className="inline-error" role="alert">
            <InfoIcon />
            <span>{error}</span>
          </div>
        )}

        <div className="landing-features" aria-label="Características">
          <span><CalendarIcon /> 7 días de previsión</span>
          <span><DatabaseIcon /> Fuentes combinadas</span>
          <span><GlobeIcon /> Ubicaciones de todo el mundo</span>
        </div>
      </main>
    </div>
  );
}

interface ResultsProps {
  forecast: AggregatedForecast;
  location: LocationCandidate;
  selectedDate: string | null;
  loading: boolean;
  error: string | null;
  onDateSelect: (date: string) => void;
  onLocationSelect: (location: LocationCandidate) => void;
}

function Results({
  forecast,
  location,
  selectedDate,
  loading,
  error,
  onDateSelect,
  onLocationSelect,
}: ResultsProps) {
  const selectedDay =
    forecast.daily_forecast.find((day) => day.date === selectedDate) ??
    forecast.daily_forecast[0];
  const selectedHours = selectedDay
    ? forecast.hourly_forecast.filter((hour) => hour.datetime.slice(0, 10) === selectedDay.date)
    : [];

  return (
    <div className="results-shell">
      <header className="topbar">
        <Brand compact />
        <LocationSearch
          forecastLoading={loading}
          onSelect={onLocationSelect}
          value={location.display_name}
          variant="compact"
        />
        <div className="topbar-source-count">
          <DatabaseIcon />
          <span>
            <strong>{forecast.providers_used.length} proveedores</strong>
            <small>en esta previsión</small>
          </span>
        </div>
      </header>

      {loading && (
        <div className="page-progress" aria-label="Cargando nueva previsión">
          <span />
        </div>
      )}

      <main className="results-main">
        <section className="location-banner">
          <span className="location-banner-icon">
            <MapPinIcon />
          </span>
          <div className="location-banner-copy">
            <h1>{location.display_name}</h1>
            <div className="location-banner-meta">
              <span>{formatCoordinate(location.latitude)}, {formatCoordinate(location.longitude)}</span>
            </div>
          </div>
        </section>

        {error && (
          <div className="notice notice--error" role="alert">
            <InfoIcon />
            <span>{error} Se mantiene la previsión anterior.</span>
          </div>
        )}

        {forecast.warnings.map((warning) => (
          <div className="notice" key={warning}>
            <InfoIcon />
            <span>{warning}</span>
          </div>
        ))}

        <DailyForecast
          days={forecast.daily_forecast}
          onSelect={onDateSelect}
          selectedDate={selectedDay?.date ?? null}
        />

        {selectedDay && <HourlyForecast day={selectedDay} hours={selectedHours} />}

        {!selectedDay && (
          <div className="empty-forecast">
            El backend no ha devuelto días disponibles para esta ubicación.
          </div>
        )}

        <aside
          aria-label="Aviso sobre la previsión"
          className="disclaimer"
          role="note"
        >
          <InfoIcon />
          <div className="disclaimer-copy">
            <strong>Previsión de carácter informativo</strong>
            <p>
              Los resultados agregan predicciones de proveedores externos y
              pueden contener errores. No deben utilizarse como única fuente
              para decisiones críticas relacionadas con emergencias,
              navegación o protección civil.
            </p>
            <small>
              La disponibilidad y calidad de los datos dependen de los
              proveedores meteorológicos y de sus condiciones de servicio.
            </small>
          </div>
        </aside>

      </main>
    </div>
  );
}

export default function App() {
  const forecastController = useRef<AbortController | null>(null);
  const [location, setLocation] = useState<LocationCandidate | null>(null);
  const [forecast, setForecast] = useState<AggregatedForecast | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => forecastController.current?.abort();
  }, []);

  async function handleLocationSelect(nextLocation: LocationCandidate) {
    forecastController.current?.abort();
    const controller = new AbortController();
    forecastController.current = controller;
    setLoading(true);
    setError(null);

    try {
      const nextForecast = await fetchAggregatedForecast(nextLocation, controller.signal);
      if (controller.signal.aborted) {
        return;
      }

      startTransition(() => {
        setLocation(nextLocation);
        setForecast(nextForecast);
        setSelectedDate(nextForecast.daily_forecast[0]?.date ?? null);
      });
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") {
        return;
      }

      setError(
        requestError instanceof Error
          ? requestError.message
          : "No se ha podido obtener la previsión.",
      );
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }

  if (!forecast || !location) {
    return (
      <Landing
        error={error}
        loading={loading}
        onLocationSelect={handleLocationSelect}
      />
    );
  }

  return (
    <Results
      error={error}
      forecast={forecast}
      loading={loading}
      location={location}
      onDateSelect={setSelectedDate}
      onLocationSelect={handleLocationSelect}
      selectedDate={selectedDate}
    />
  );
}
