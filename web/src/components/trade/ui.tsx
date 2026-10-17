import type { ReactNode } from "react";
import { cn } from "@/lib/trade/format";
import type { Mode } from "@/lib/trade/types";

export function BrandMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 160 160"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="nemt-brand-gradient" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor="#F5F8FA" />
          <stop offset=".53" stopColor="#CCD4DE" />
          <stop offset=".54" stopColor="#00D8EB" />
          <stop offset="1" stopColor="#00A5D9" />
        </linearGradient>
      </defs>
      <path
        d="M35 122 L40 38 L56 38 L104 98 L109 38 L125 30 L119 122 L104 122 L55 61 L50 122 Z"
        fill="url(#nemt-brand-gradient)"
      />
      <path
        d="M22 91 C49 74 63 119 87 95 S117 67 139 89"
        stroke="#10DBE9"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

type IconName =
  | "overview"
  | "market"
  | "trade"
  | "orders"
  | "settings"
  | "refresh"
  | "warning"
  | "shield"
  | "wifiOff"
  | "check"
  | "close"
  | "chevronRight"
  | "lock"
  | "external"
  | "pause"
  | "play"
  | "download"
  | "info"
  | "clock"
  | "logout";

const ICON_PATHS: Record<IconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  market: (
    <>
      <path d="M4 4v16h16" />
      <path d="m7 15 4-5 3 2.5L20 6" />
    </>
  ),
  trade: (
    <>
      <path d="M7 7h11l-3-3" />
      <path d="M17 17H6l3 3" />
    </>
  ),
  orders: (
    <>
      <path d="M8 6h12M8 12h12M8 18h12" />
      <path d="M4 6h.01M4 12h.01M4 18h.01" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.66 8.5a1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.1A1.7 1.7 0 0 0 15.5 4.66a1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.1.34.3.66.6 1 .3.24.68.4 1.1.4h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.7.6Z" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 11a8 8 0 1 0-2.34 5.66" />
      <path d="M20 4v7h-7" />
    </>
  ),
  warning: (
    <>
      <path d="m12 3 9.5 17h-19Z" />
      <path d="M12 9v5M12 17.5h.01" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 4.5 6v5.5c0 4.6 3.2 8 7.5 9.5 4.3-1.5 7.5-4.9 7.5-9.5V6Z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  wifiOff: (
    <>
      <path d="m3 3 18 18" />
      <path d="M8.5 8.7A9 9 0 0 1 21 10M2.5 9.5a15 15 0 0 1 3.2-1.7" />
      <path d="M5 13a10 10 0 0 1 3-1.4M14 15.5a5 5 0 0 0-4 0" />
      <path d="M12 20h.01" />
    </>
  ),
  check: <path d="m5 12 4.5 4.5L19 7" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  chevronRight: <path d="m9 5 7 7-7 7" />,
  lock: (
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>
  ),
  external: (
    <>
      <path d="M14 4h6v6M20 4l-9 9" />
      <path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" />
    </>
  ),
  pause: (
    <>
      <rect x="6" y="4" width="4" height="16" rx="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" />
    </>
  ),
  play: <path d="m8 5 11 7-11 7Z" />,
  download: (
    <>
      <path d="M12 3v12m0 0 4-4m-4 4-4-4" />
      <path d="M5 19h14" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  logout: (
    <>
      <path d="M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </>
  ),
};

export function Icon({
  name,
  size = 18,
  className,
  strokeWidth = 1.8,
}: {
  name: IconName;
  size?: number;
  className?: string;
  strokeWidth?: number;
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
      {ICON_PATHS[name]}
    </svg>
  );
}

const TONE_CLASSES = {
  ok: "text-emerald-400",
  warn: "text-amber-300",
  bad: "text-rose-400",
  info: "text-cyan-300",
  muted: "text-slate-500",
} as const;

export type Tone = keyof typeof TONE_CLASSES;

export function StatusDot({
  tone = "muted",
  pulse = false,
  size = 6,
}: {
  tone?: Tone;
  pulse?: boolean;
  size?: number;
}) {
  return (
    <span
      className={cn("trade-dot", TONE_CLASSES[tone], pulse && "trade-dot-pulse")}
      style={{ width: size, height: size }}
    />
  );
}

export function Spinner({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={cn("trade-spin", className)}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.18" strokeWidth="2.5" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function SectionHeader({
  title,
  hint,
  action,
  className,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-end justify-between gap-3 mb-3", className)}>
      <div className="min-w-0">
        <h2 className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
          {title}
        </h2>
        {hint ? <p className="text-[11px] text-slate-500 mt-0.5 truncate">{hint}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function ModeBadge({ mode, className }: { mode: Mode; className?: string }) {
  const style =
    mode === "DEMO"
      ? "trade-chip-amber"
      : mode === "TESTNET"
        ? "trade-chip-cyan"
        : "trade-chip-danger";
  return (
    <span className={cn("trade-chip", style, className)}>
      <span className="trade-dot" />
      {mode}
    </span>
  );
}

export function SourceBadge({
  source,
  stale,
}: {
  source: "binance" | "demo" | null | undefined;
  stale?: boolean;
}) {
  if (!source) {
    return <span className="trade-chip">NO FEED</span>;
  }
  if (stale) {
    return (
      <span className="trade-chip trade-chip-danger">
        <span className="trade-dot" />
        STALE
      </span>
    );
  }
  return (
    <span className={cn("trade-chip", source === "demo" ? "trade-chip-amber" : "trade-chip-cyan")}>
      <span className="trade-dot" />
      {source === "demo" ? "SIM 模拟" : "BINANCE 实时"}
    </span>
  );
}

export function EmptyState({
  icon = "info",
  title,
  body,
  action,
}: {
  icon?: IconName;
  title: string;
  body?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
      <div className="w-12 h-12 rounded-2xl border border-white/8 bg-white/[0.03] flex items-center justify-center text-slate-500 mb-3">
        <Icon name={icon} size={22} />
      </div>
      <p className="text-sm font-semibold text-slate-300">{title}</p>
      {body ? <p className="text-xs text-slate-500 mt-1 max-w-[260px] leading-relaxed">{body}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function Divider({ className }: { className?: string }) {
  return <div className={cn("h-px w-full bg-white/[0.06]", className)} />;
}

export function KeyValue({
  label,
  value,
  tone,
}: {
  label: string;
  value: ReactNode;
  tone?: "up" | "down" | "muted" | "warn";
}) {
  const color =
    tone === "up"
      ? "text-emerald-400"
      : tone === "down"
        ? "text-rose-400"
        : tone === "warn"
          ? "text-amber-300"
          : tone === "muted"
            ? "text-slate-400"
            : "text-slate-200";
  return (
    <div className="flex items-center justify-between gap-4 min-h-[28px]">
      <span className="text-[11px] text-slate-500">{label}</span>
      <span className={cn("trade-number text-[12px] text-right", color)}>{value}</span>
    </div>
  );
}
