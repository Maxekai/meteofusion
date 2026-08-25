import type { CSSProperties } from "react";

import {
  conditionLabel,
  formatHour,
  formatLongDate,
  formatNumber,
} from "../lib/format";
import type {
  AggregatedDailyForecastPoint,
  AggregatedHourlyForecastPoint,
} from "../types/weather";
import { MetricTriplet } from "./MetricTriplet";
import { WeatherIcon } from "./WeatherIcon";

interface HourlyForecastProps {
  day: AggregatedDailyForecastPoint;
  hours: AggregatedHourlyForecastPoint[];
}

function MetricColumnHeader({
  label,
  variant = "aggregate",
}: {
  label: string;
  variant?: "aggregate" | "consensus";
}) {
  const labels =
    variant === "consensus"
      ? ["bajo", "consenso", "alto"]
      : ["mín.", "media", "máx."];

  return (
    <span
      className={`metric-column-header metric-column-header--${variant}`}
      role="columnheader"
    >
      <strong>{label}</strong>
      <small>
        <span>{labels[0]}</span>
        <b
          title={
            variant === "consensus" ? "Mediana de los proveedores" : undefined
          }
        >
          {labels[1]}
        </b>
        <span>{labels[2]}</span>
      </small>
    </span>
  );
}

function ProbabilityCell({
  stat,
}: {
  stat: AggregatedHourlyForecastPoint["precipitation_probability"];
}) {
  const average = Math.min(Math.max(stat.avg ?? 0, 0), 100);
  const ringStyle = {
    "--probability-angle": `${average * 3.6}deg`,
  } as CSSProperties;

  return (
    <div className="probability-gauge">
      <span className="probability-ring" style={ringStyle} aria-hidden="true">
        <span />
      </span>
      <span className="probability-summary">
        <strong className="probability-average">{formatNumber(stat.avg, 0)}%</strong>
        <small className="probability-range">
          {formatNumber(stat.min, 0)}–{formatNumber(stat.max, 0)}%
        </small>
      </span>
    </div>
  );
}

interface InlineMetricProps {
  className: string;
  label: string;
  unit: string;
  value: number | null;
}

function InlineMetric({ className, label, unit, value }: InlineMetricProps) {
  return (
    <span
      className={`hour-inline-metric ${className}`}
      data-label={label}
      role="cell"
    >
      <strong>
        {formatNumber(value)}{value === null ? "" : unit}
      </strong>
    </span>
  );
}

export function HourlyForecast({ day, hours }: HourlyForecastProps) {
  return (
    <section className="day-detail" aria-labelledby="day-detail-title">
      <div className="hourly-panel">
        <header className="hourly-toolbar">
          <div>
            <span className="section-kicker">Predicción hora a hora</span>
            <h2 id="day-detail-title">{formatLongDate(day.date)}</h2>
          </div>
        </header>

        {hours.length === 0 ? (
          <div className="empty-hours">
            No hay información horaria disponible para este día.
          </div>
        ) : (
          <div className="hourly-table-wrap">
            <div
              className="hourly-table"
              role="table"
              aria-label={`Previsión horaria para ${formatLongDate(day.date)}`}
            >
              <div className="hourly-row hourly-row--head" role="row">
                <span role="columnheader">Hora</span>
                <span role="columnheader">Tiempo</span>
                <MetricColumnHeader
                  label="Temperatura (°C)"
                  variant="consensus"
                />
                <MetricColumnHeader label="Precipitación (mm)" />
                <MetricColumnHeader label="Nieve (cm)" />
                <span role="columnheader">Probabilidad</span>
                <span role="columnheader">Sensación</span>
                <span role="columnheader">Humedad</span>
                <span role="columnheader">Viento</span>
              </div>

              {hours.map((hour) => {
                const hourLabel = formatHour(hour.datetime);

                return (
                  <div className="hourly-row-group" key={hour.datetime}>
                    <div className="hourly-row" role="row">
                      <span className="hour-time" data-label="Hora" role="cell">
                        {hourLabel}
                      </span>

                      <span className="hour-condition" data-label="Tiempo" role="cell">
                        <WeatherIcon condition={hour.condition} size={40} />
                        <span>
                          <strong>{conditionLabel(hour.condition)}</strong>
                        </span>
                      </span>

                      <span className="hour-metric hour-metric--temperature" data-label="Temperatura" role="cell">
                        <MetricTriplet stat={hour.temperature_c} unit="°" />
                      </span>

                      <span className="hour-metric hour-metric--precipitation" data-label="Precipitación" role="cell">
                        <MetricTriplet digits={1} stat={hour.precipitation_total} />
                      </span>

                      <span className="hour-metric hour-metric--snow" data-label="Nieve" role="cell">
                        <MetricTriplet stat={hour.precipitation_snow} />
                      </span>

                      <span className="hour-probability" data-label="Probabilidad" role="cell">
                        <ProbabilityCell stat={hour.precipitation_probability} />
                      </span>

                      <InlineMetric
                        className="hour-inline-metric--feels"
                        label="Sensación"
                        unit="°C"
                        value={hour.apparent_temperature_c}
                      />

                      <InlineMetric
                        className="hour-inline-metric--humidity"
                        label="Humedad"
                        unit="%"
                        value={hour.humidity_percent}
                      />

                      <InlineMetric
                        className="hour-inline-metric--wind"
                        label="Viento"
                        unit=" km/h"
                        value={hour.wind_speed_kmh}
                      />

                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
