interface BrandProps {
  compact?: boolean;
}

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 72 58" aria-hidden="true">
      <g stroke="#f6ab00" strokeWidth="2.4" strokeLinecap="round">
        <path d="M46 3v6M46 33v6M28 21h6M58 21h6M33.3 8.3l4.2 4.2M54.5 29.5l4.2 4.2M33.3 33.7l4.2-4.2M54.5 12.5l4.2-4.2" />
      </g>
      <circle cx="46" cy="21" r="10" fill="#ffbd20" />
      <path
        d="M16 49h37.5a10 10 0 0 0 1.4-19.9A15.5 15.5 0 0 0 25 26.7 11.5 11.5 0 0 0 16 49Z"
        fill="#1479ee"
      />
      <path
        d="M17 49h36.5a10 10 0 0 0 1.4-19.9c-3.4 7.1-11.1 12.7-20.5 14.5-6.7 1.3-12.9.6-17.4-1.5Z"
        fill="#0865d4"
        opacity=".45"
      />
    </svg>
  );
}

export function Brand({ compact = false }: BrandProps) {
  return (
    <div className={`brand ${compact ? "brand--compact" : ""}`}>
      <BrandMark />
      <div className="brand-copy">
        <span className="brand-name">MeteoFusion</span>
      </div>
    </div>
  );
}
