import type { ReactNode } from "react";
import { cn } from "@/lib/trade/format";

/* --------------------------------------------------------------------------
   NEMT Studio V3 editorial primitives.
   Pure presentation. No data, no fabricated metrics.
   -------------------------------------------------------------------------- */

export function EditorialPage({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("nsx-page", className)}>{children}</div>;
}

export function Masthead({
  kicker,
  title,
  accent,
  lead,
  actions,
  issue,
  compact = false,
}: {
  kicker: string;
  title: ReactNode;
  accent?: ReactNode;
  lead?: ReactNode;
  actions?: ReactNode;
  issue?: { label: string; value: ReactNode; note: ReactNode };
  compact?: boolean;
}) {
  return (
    <header className={cn("nsx-masthead", compact && "is-compact")}>
      <div className="nsx-masthead-copy">
        <p className="nsx-kicker">{kicker}</p>
        <h1 className="nsx-title">
          {title}
          {accent ? (
            <>
              <br />
              <em>{accent}</em>
            </>
          ) : null}
        </h1>
        {lead ? <p className="nsx-lead">{lead}</p> : null}
      </div>
      <div className="nsx-masthead-aside">
        {issue ? (
          <div className="nsx-issue">
            <span>{issue.label}</span>
            <strong>{issue.value}</strong>
            <small>{issue.note}</small>
          </div>
        ) : null}
        {actions ? <div className="nsx-masthead-actions">{actions}</div> : null}
      </div>
    </header>
  );
}

export interface EditorialMetric {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  accent?: boolean;
  mono?: boolean;
}

export function MetricTape({
  items,
  className,
}: {
  items: EditorialMetric[];
  className?: string;
}) {
  return (
    <dl className={cn("nsx-tape", className)}>
      {items.map((item) => (
        <div className="nsx-tape-item" key={item.label}>
          <dt>{item.label}</dt>
          <dd
            className={cn(
              "nsx-tape-value",
              item.accent && "is-accent",
              item.mono === false && "is-sans"
            )}
          >
            {item.value}
          </dd>
          {item.note ? <p>{item.note}</p> : null}
        </div>
      ))}
    </dl>
  );
}

export function Section({
  index,
  label,
  title,
  description,
  action,
  children,
  className,
  bodyClassName,
  id,
}: {
  index: string;
  label: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  id?: string;
}) {
  return (
    <section className={cn("nsx-section", className)} id={id}>
      <header className="nsx-section-head">
        <div className="nsx-section-label">
          <span>{index}</span>
          <p>{label}</p>
        </div>
        <div className="nsx-section-copy">
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
        {action ? <div className="nsx-section-action">{action}</div> : null}
      </header>
      <div className={cn("nsx-section-body", bodyClassName)}>{children}</div>
    </section>
  );
}

export function EmptyBlock({
  mark = "—",
  title,
  body,
  meta,
  action,
  className,
}: {
  mark?: ReactNode;
  title: ReactNode;
  body?: ReactNode;
  meta?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("nsx-empty", className)}>
      <span className="nsx-empty-mark" aria-hidden="true">
        {mark}
      </span>
      <div className="nsx-empty-copy">
        <h3>{title}</h3>
        {body ? <p>{body}</p> : null}
        {meta ? <span className="nsx-empty-meta">{meta}</span> : null}
      </div>
      {action ? <div className="nsx-empty-action">{action}</div> : null}
    </div>
  );
}

export function StatusTag({
  tone = "muted",
  children,
  className,
}: {
  tone?: "ok" | "warn" | "bad" | "muted" | "brand";
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("nsx-tag", `is-${tone}`, className)}>
      <i aria-hidden="true" />
      {children}
    </span>
  );
}

export interface PipelineStep {
  label: string;
  caption?: string;
  state?: "done" | "current" | "pending" | "blocked";
}

export function Pipeline({
  steps,
  ariaLabel,
  className,
  vertical = false,
}: {
  steps: PipelineStep[];
  ariaLabel: string;
  className?: string;
  vertical?: boolean;
}) {
  return (
    <ol
      className={cn("nsx-pipeline", vertical && "is-vertical", className)}
      aria-label={ariaLabel}
    >
      {steps.map((step, index) => (
        <li key={`${step.label}-${index}`} data-state={step.state ?? "pending"}>
          <span className="nsx-pipeline-index">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="nsx-pipeline-copy">
            <strong>{step.label}</strong>
            {step.caption ? <em>{step.caption}</em> : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function EditorialLink({
  onClick,
  children,
  disabled = false,
  title,
}: {
  onClick?: () => void;
  children: ReactNode;
  disabled?: boolean;
  title?: string;
}) {
  return (
    <button
      type="button"
      className="nsx-link"
      onClick={onClick}
      disabled={disabled}
      title={title}
    >
      {children}
      <span aria-hidden="true">↗</span>
    </button>
  );
}

export function PageFootnote({
  left = "NEMT STUDIO",
  center,
  right = "NON-EQUILIBRIUM / 2026",
}: {
  left?: ReactNode;
  center: ReactNode;
  right?: ReactNode;
}) {
  return (
    <footer className="nsx-page-note">
      <span>{left}</span>
      <p>{center}</p>
      <span>{right}</span>
    </footer>
  );
}
