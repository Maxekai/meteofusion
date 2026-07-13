import { formatNumber } from "../lib/format";
import type { AggregatedStat } from "../types/weather";

interface MetricTripletProps {
  stat: AggregatedStat;
  unit?: string;
  digits?: number;
  compact?: boolean;
}

export function MetricTriplet({
  stat,
  unit = "",
  digits = 0,
  compact = false,
}: MetricTripletProps) {
  const values = [stat.min, stat.avg, stat.max];

  return (
    <div className={`metric-triplet ${compact ? "metric-triplet--compact" : ""}`}>
      {values.map((value, index) => (
        <span className={index === 1 ? "metric-value metric-value--avg" : "metric-value"} key={index}>
          {formatNumber(value, digits)}{value === null ? "" : unit}
        </span>
      ))}
    </div>
  );
}
