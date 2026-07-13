import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const defaults = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export function SearchIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4 4" />
    </svg>
  );
}

export function MapPinIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

export function DatabaseIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <ellipse cx="12" cy="5" rx="7.5" ry="3" />
      <path d="M4.5 5v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V5" />
      <path d="M4.5 11v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6" />
    </svg>
  );
}

export function CalendarIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <rect x="3" y="5" width="18" height="16" rx="3" />
      <path d="M8 3v4M16 3v4M3 10h18" />
    </svg>
  );
}

export function InfoIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7.5h.01" />
    </svg>
  );
}

export function DropletIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M12 2.7S5.5 10 5.5 15a6.5 6.5 0 0 0 13 0C18.5 10 12 2.7 12 2.7Z" />
    </svg>
  );
}

export function SnowIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M12 2v20M4 6.5l16 11M4 17.5l16-11" />
      <path d="m9 4 3 2 3-2M9 20l3-2 3 2M5 10l.2-3.6L8.5 5M19 14l-.2 3.6-3.3 1.4M5 14l.2 3.6L8.5 19M19 10l-.2-3.6L15.5 5" />
    </svg>
  );
}

export function WindIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M3 8h10.5a2.5 2.5 0 1 0-2.2-3.7" />
      <path d="M3 12h16a2.5 2.5 0 1 1-2.2 3.7M3 16h7" />
    </svg>
  );
}

export function ThermometerIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M9 14.7V5a3 3 0 0 1 6 0v9.7a5 5 0 1 1-6 0Z" />
      <path d="M12 8v9" />
    </svg>
  );
}

export function GlobeIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="M5 12h14M14 7l5 5-5 5" />
    </svg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="m9 5 7 7-7 7" />
    </svg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <svg {...defaults} {...props}>
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  );
}
