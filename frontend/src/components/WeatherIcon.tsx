import type { WeatherCondition } from "../types/weather";

interface WeatherIconProps {
  condition: WeatherCondition;
  size?: number;
  className?: string;
}

function Sun() {
  return (
    <>
      <g stroke="#f7a900" strokeWidth="2.8" strokeLinecap="round">
        <path d="M24 5v6M24 37v6M5 24h6M37 24h6M10.6 10.6l4.2 4.2M33.2 33.2l4.2 4.2M10.6 37.4l4.2-4.2M33.2 14.8l4.2-4.2" />
      </g>
      <circle cx="24" cy="24" r="9.5" fill="#ffbd20" />
    </>
  );
}

function Cloud({ dark = false }: { dark?: boolean }) {
  return (
    <path
      d="M13 36.5h25.3a7.7 7.7 0 0 0 1.3-15.3A12.7 12.7 0 0 0 15 19.1a8.8 8.8 0 0 0-2 17.4Z"
      fill={dark ? "#64748b" : "#a9bdd5"}
    />
  );
}

export function WeatherIcon({
  condition,
  size = 64,
  className = "",
}: WeatherIconProps) {
  return (
    <svg
      className={`weather-icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
    >
      {condition === "sunny" && <Sun />}
      {condition === "partly_cloudy" && (
        <>
          <g transform="translate(-5 -6) scale(.78)">
            <Sun />
          </g>
          <Cloud />
        </>
      )}
      {condition === "cloudy" && (
        <>
          <path
            d="M9 31h21a6.5 6.5 0 0 0 .6-13 10.5 10.5 0 0 0-20.2-1.5A7.3 7.3 0 0 0 9 31Z"
            fill="#aebed2"
          />
          <g transform="translate(4 4)">
            <Cloud dark />
          </g>
        </>
      )}
      {condition === "rain" && (
        <>
          <g transform="translate(0 -5)">
            <Cloud dark />
          </g>
          <g stroke="#1688f8" strokeWidth="3" strokeLinecap="round">
            <path d="m16 35-2 5M26 35l-2 5M36 35l-2 5" />
          </g>
        </>
      )}
      {condition === "snow" && (
        <>
          <g transform="translate(0 -6)">
            <Cloud dark />
          </g>
          <g fill="#56aef8">
            <circle cx="15" cy="38" r="2" />
            <circle cx="25" cy="35" r="2" />
            <circle cx="35" cy="39" r="2" />
          </g>
        </>
      )}
      {condition === "unknown" && (
        <>
          <Cloud />
          <text
            x="24"
            y="32"
            textAnchor="middle"
            fill="#475569"
            fontSize="18"
            fontWeight="800"
          >
            ?
          </text>
        </>
      )}
    </svg>
  );
}
