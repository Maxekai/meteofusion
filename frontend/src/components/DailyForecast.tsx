import type { CSSProperties } from "react";

import {
  formatDayMonth,
  formatDayName,
  formatNumber,
} from "../lib/format";
import type {
  AggregatedDailyForecastPoint,
  AggregatedStat,
} from "../types/weather";
import { DropletIcon, ThermometerIcon } from "./Icons";
import { WeatherIcon } from "./WeatherIcon";

interface DailyForecastProps {
  days: AggregatedDailyForecastPoint[];
  selectedDate: string | null;
  onSelect: (date: string) => void;
}

interface DailyMetricProps {
  digits?: number;
  icon: "temperature" | "precipitation";
  label: string;
  stat: AggregatedStat;
  tone: "blue" | "orange" | "precipitation";
  unit?: string;
}

function DailyMetric({
  digits = 0,
  icon,
  label,
  stat,
  tone,
  unit = "",
}: DailyMetricProps) {
  const MetricIcon = icon === "temperature" ? ThermometerIcon : DropletIcon;
  const formatValue = (value: number | null) =>
    `${formatNumber(value, digits)}${value === null ? "" : unit}`;

  return (
    <span className={`day-temperature day-temperature--${tone}`}>
      <span className="day-temperature-label">
        <MetricIcon /> {label}
      </span>
      <span className="day-temperature-values">
        <span>{formatValue(stat.min)}</span>
        <strong>{formatValue(stat.avg)}</strong>
        <span>{formatValue(stat.max)}</span>
      </span>
    </span>
  );
}

export function DailyForecast({
  days,
  selectedDate,
  onSelect,
}: DailyForecastProps) {
  return (
    <section className="daily-section" aria-labelledby="daily-title">
      <div className="section-heading-row">
        <div>
          <h2 id="daily-title">Próximos {days.length} días</h2>
          <p>Selecciona un día para consultar todas sus horas</p>
        </div>
      </div>

      <div className="daily-scroll">
        <div className="daily-grid">
          {days.map((day, index) => {
            const isSelected = day.date === selectedDate;

            return (
              <button
                aria-pressed={isSelected}
                className={`day-card ${isSelected ? "day-card--selected" : ""}`}
                key={day.date}
                onClick={() => onSelect(day.date)}
                style={{ "--card-index": index } as CSSProperties}
                type="button"
              >
                <span className="day-card-topline">
                  <span className="day-name">{formatDayName(day.date)}</span>
                  <span className="day-date-separator" aria-hidden="true">-</span>
                  <span className="day-date">{formatDayMonth(day.date)}</span>
                </span>

                <WeatherIcon condition={day.condition} size={58} />

                <DailyMetric
                  icon="temperature"
                  label="Mínima (°C)"
                  stat={day.temperature_min_c}
                  tone="blue"
                  unit="°"
                />

                <DailyMetric
                  icon="temperature"
                  label="Máxima (°C)"
                  stat={day.temperature_max_c}
                  tone="orange"
                  unit="°"
                />

                <DailyMetric
                  digits={1}
                  icon="precipitation"
                  label="Precipitación total (mm)"
                  stat={day.precipitation_total}
                  tone="precipitation"
                />

              </button>
            );
          })}
        </div>
      </div>

    </section>
  );
}
