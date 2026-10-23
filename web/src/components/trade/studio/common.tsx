import type { ReactNode } from "react";
import type { Mode } from "@/lib/trade/types";
import { StudioIcon, type StudioIconName } from "./icons";

export function Spinner({ size = 16 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className="ns-spin"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.18" strokeWidth="2.5" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function ModePill({ mode, compact = false }: { mode: Mode; compact?: boolean }) {
  const label =
    mode === "DEMO" ? "DEMO" : mode === "TESTNET" ? "TESTNET" : "LIVE";
  return (
    <span
      className={`ns-mode ns-mode-${mode.toLowerCase()}${compact ? " ns-mode-compact" : ""}`}
      title={
        mode === "DEMO"
          ? "模拟环境：订单进入本地模拟账本，不涉及真实资金"
          : mode === "TESTNET"
            ? "测试网环境：使用测试资金"
            : "实盘环境：真实资金"
      }
    >
      <span className="ns-mode-dot" />
      {label}
      {!compact ? <span className="ns-mode-suffix">模拟</span> : null}
    </span>
  );
}

export function StatusDot({
  tone = "ok",
  pulse = false,
  size,
}: {
  tone?: "ok" | "warn" | "bad" | "muted" | "brand";
  pulse?: boolean;
  size?: number;
}) {
  return (
    <span
      className={`ns-status-dot ns-status-${tone}${pulse ? " ns-status-pulse" : ""}`}
      style={size ? { width: size, height: size } : undefined}
      aria-hidden="true"
    />
  );
}

export function CardHeader({
  title,
  hint,
  action,
  className = "",
}: {
  title: ReactNode;
  hint?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`ns-card-head ${className}`.trim()}>
      <div className="ns-card-head-copy">
        <h2 className="ns-card-title">{title}</h2>
        {hint ? <p className="ns-card-hint">{hint}</p> : null}
      </div>
      {action ? <div className="ns-card-action">{action}</div> : null}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  icon = "orders",
  action,
  compact = false,
}: {
  title: string;
  body?: string;
  icon?: StudioIconName;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div className={`ns-empty${compact ? " ns-empty-compact" : ""}`}>
      <span className="ns-empty-icon">
        <StudioIcon name={icon} size={compact ? 18 : 22} />
      </span>
      <p className="ns-empty-title">{title}</p>
      {body ? <p className="ns-empty-body">{body}</p> : null}
      {action ? <div className="ns-empty-action">{action}</div> : null}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <span className={`ns-skeleton ${className}`.trim()} aria-hidden="true" />;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="ns-page-header">
      <div className="ns-page-heading">
        <p className="ns-page-eyebrow">{eyebrow}</p>
        <div className="ns-page-title-row">
          <h1 className="ns-page-title">{title}</h1>
        </div>
        {description ? <p className="ns-page-description">{description}</p> : null}
      </div>
      {actions ? <div className="ns-page-actions">{actions}</div> : null}
    </header>
  );
}

export function SourceTag({
  source,
  stale,
}: {
  source: "binance" | "demo" | null | undefined;
  stale?: boolean;
}) {
  if (!source) {
    return <span className="ns-source ns-source-none">无行情</span>;
  }
  if (stale) {
    return (
      <span className="ns-source ns-source-warn">
        <span className="ns-source-dot" />
        数据延迟
      </span>
    );
  }
  return source === "demo" ? (
    <span className="ns-source ns-source-sim">
      <span className="ns-source-dot" />
      模拟行情
    </span>
  ) : (
    <span className="ns-source">
      <span className="ns-source-dot" />
      Binance
    </span>
  );
}

export function InlineAlert({
  tone = "neutral",
  children,
  action,
}: {
  tone?: "neutral" | "warn" | "danger" | "success" | "info";
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={`ns-inline-alert ns-inline-alert-${tone}`} role={tone === "danger" ? "alert" : undefined}>
      <span className="ns-inline-alert-body">{children}</span>
      {action ? <span className="ns-inline-alert-action">{action}</span> : null}
    </div>
  );
}

export function MiniStatus({
  label,
  value,
  tone,
}: {
  label: string;
  value: ReactNode;
  tone?: "up" | "down" | "neutral";
}) {
  return (
    <div className="ns-mini-status">
      <span className="ns-mini-status-label">{label}</span>
      <span className={`ns-mini-status-value ${tone ? `ns-text-${tone}` : ""}`.trim()}>
        {value}
      </span>
    </div>
  );
}
