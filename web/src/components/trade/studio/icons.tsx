import type { ReactNode } from "react";

export type StudioIconName =
  | "overview"
  | "markets"
  | "trade"
  | "strategies"
  | "research"
  | "experiments"
  | "orders"
  | "assets"
  | "settings"
  | "menu"
  | "close"
  | "refresh"
  | "logout"
  | "chevronDown"
  | "chevronLeft"
  | "chevronRight"
  | "arrowUpRight"
  | "shield"
  | "lock"
  | "clock"
  | "warning"
  | "check"
  | "info"
  | "external"
  | "plus"
  | "cpu"
  | "fileText"
  | "database"
  | "activity"
  | "play"
  | "pause"
  | "sliders";

const PATHS: Record<StudioIconName, ReactNode> = {
  overview: (
    <>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.2" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.2" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.2" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.2" />
    </>
  ),
  markets: (
    <>
      <path d="M7 3v3.5M7 17.5V21M17 3v5M17 15.5V21" />
      <rect x="4" y="6.5" width="6" height="11" rx="1" />
      <rect x="14" y="8" width="6" height="7.5" rx="1" />
    </>
  ),
  trade: (
    <>
      <path d="M4 8h14M14 4l4 4-4 4" />
      <path d="M20 16H6M10 12l-4 4 4 4" />
    </>
  ),
  strategies: (
    <>
      <path d="M4 7h9M17 7h3M4 17h3M11 17h9" />
      <circle cx="15" cy="7" r="2" />
      <circle cx="9" cy="17" r="2" />
    </>
  ),
  research: (
    <>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v17H6.5A2.5 2.5 0 0 0 4 22.5Z" />
      <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v17h4.5A2.5 2.5 0 0 1 20 22.5Z" />
    </>
  ),
  experiments: (
    <>
      <path d="M9 3h6M10 3v5.2L5.2 17a3 3 0 0 0 2.7 4.5h8.2a3 3 0 0 0 2.7-4.5L14 8.2V3" />
      <path d="M7.3 14h9.4" />
    </>
  ),
  orders: (
    <>
      <rect x="5" y="3.5" width="14" height="17" rx="2" />
      <path d="M9 8h6M9 12h6M9 16h4" />
    </>
  ),
  assets: (
    <>
      <path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H18a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6.5A2.5 2.5 0 0 1 4 17.5Z" />
      <path d="M4 8.5h16M15 13h5v4h-5a2 2 0 0 1 0-4Z" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.66 8.5a1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.1A1.7 1.7 0 0 0 15.5 4.66a1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.1.34.3.66.6 1 .3.24.68.4 1.1.4h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.7.6Z" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  refresh: (
    <>
      <path d="M20 11a8 8 0 1 0-2.34 5.66" />
      <path d="M20 4v7h-7" />
    </>
  ),
  logout: (
    <>
      <path d="M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4" />
      <path d="m16 17 5-5-5-5M21 12H9" />
    </>
  ),
  chevronDown: <path d="m6 9 6 6 6-6" />,
  chevronLeft: <path d="m15 18-6-6 6-6" />,
  chevronRight: <path d="m9 18 6-6-6-6" />,
  arrowUpRight: <path d="M7 17 17 7M8 7h9v9" />,
  shield: (
    <>
      <path d="M12 3 4.5 6v5.5c0 4.6 3.2 8 7.5 9.5 4.3-1.5 7.5-4.9 7.5-9.5V6Z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  lock: (
    <>
      <rect x="4.5" y="10" width="15" height="10.5" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  warning: (
    <>
      <path d="m12 3 9.5 17h-19Z" />
      <path d="M12 9v5M12 17.5h.01" />
    </>
  ),
  check: <path d="m5 12 4.5 4.5L19 7" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),
  external: (
    <>
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  cpu: (
    <>
      <rect x="6.5" y="6.5" width="11" height="11" rx="2" />
      <rect x="9.5" y="9.5" width="5" height="5" rx="1" />
      <path d="M9 3v3.5M15 3v3.5M9 17.5V21M15 17.5V21M3 9h3.5M3 15h3.5M17.5 9H21M17.5 15H21" />
    </>
  ),
  fileText: (
    <>
      <path d="M6 3h8l4 4v14H6Z" />
      <path d="M14 3v4h4M9 12h6M9 16h6" />
    </>
  ),
  database: (
    <>
      <ellipse cx="12" cy="5.5" rx="7.5" ry="3" />
      <path d="M4.5 5.5v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6" />
      <path d="M4.5 11.5v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6" />
    </>
  ),
  activity: <path d="M3 12h4l2.5-6 5 12 2.5-6h4" />,
  play: <path d="m8 5 11 7-11 7Z" />,
  pause: (
    <>
      <rect x="6" y="4" width="4" height="16" rx="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" />
    </>
  ),
  sliders: (
    <>
      <path d="M4 6h16M4 12h16M4 18h16" />
      <circle cx="9" cy="6" r="2" fill="var(--ns-surface)" />
      <circle cx="15" cy="12" r="2" fill="var(--ns-surface)" />
      <circle cx="7" cy="18" r="2" fill="var(--ns-surface)" />
    </>
  ),
};

export function StudioIcon({
  name,
  size = 18,
  strokeWidth = 1.7,
  className,
}: {
  name: StudioIconName;
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}

export function StudioBrandMark({ size = 30 }: { size?: number }) {
  return (
    <span className="ns-brand-mark" style={{ width: size, height: size }} aria-hidden="true">
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none">
        <path
          d="M18 5H6v14h12M6 12h9"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="18" cy="19" r="1.6" fill="currentColor" />
      </svg>
    </span>
  );
}

export function StudioBrand({ compact = false }: { compact?: boolean }) {
  return (
    <span className="ns-brand">
      <StudioBrandMark size={compact ? 28 : 32} />
      <span className="ns-brand-type">
        <span className="ns-brand-name">emergentix</span>
        <span className="ns-brand-product">涌现流派</span>
      </span>
    </span>
  );
}
