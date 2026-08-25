import { formatNumber } from "../lib/format";
import type {
  AggregatedStat,
  TemperatureConsensusStat,
} from "../types/weather";

type TripletStat = AggregatedStat | TemperatureConsensusStat;

interface MetricTripletProps {
  stat: TripletStat;
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
  const isConsensus = "central" in stat;
  const values = isConsensus
    ? [stat.consensus_low, stat.central, stat.consensus_high]
    : [stat.min, stat.avg, stat.max];

  return (
    <div
      className={`metric-triplet ${
        isConsensus ? "metric-triplet--consensus" : ""
      } ${compact ? "metric-triplet--compact" : ""}`}
    >
      {values.map((value, index) => (
        <span
          className={
            index === 1
              ? "metric-value metric-value--central"
              : "metric-value"
          }
          key={index}
        >
          {formatNumber(value, digits)}{value === null ? "" : unit}
        </span>
      ))}
    </div>
  );
}
