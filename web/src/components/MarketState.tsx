import { Card } from "./Card";
import type { MarketPhase, Sentiment } from "@/lib/types";
import { classNames, formatPercent } from "@/lib/format";

const PHASE_STYLES: Record<MarketPhase, { label: string; cls: string; dot: string }> = {
  ACCUMULATION: { label: "Accumulation", cls: "text-blue-300 bg-blue-500/10 ring-blue-500/30", dot: "bg-blue-400" },
  MARKUP:       { label: "Mark-up",       cls: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30", dot: "bg-emerald-400" },
  DISTRIBUTION: { label: "Distribution",  cls: "text-amber-300 bg-amber-500/10 ring-amber-500/30", dot: "bg-amber-400" },
  MARKDOWN:     { label: "Mark-down",     cls: "text-rose-300 bg-rose-500/10 ring-rose-500/30", dot: "bg-rose-400" },
  RECOVERY:     { label: "Recovery",      cls: "text-cyan-300 bg-cyan-500/10 ring-cyan-500/30", dot: "bg-cyan-400" },
  UNKNOWN:      { label: "Unknown",       cls: "text-slate-300 bg-slate-500/10 ring-slate-500/30", dot: "bg-slate-400" },
};

const SENTIMENT_STYLES: Record<Sentiment, string> = {
  BULLISH: "text-emerald-300",
  BEARISH: "text-rose-300",
  NEUTRAL: "text-slate-300",
  CAUTIOUS: "text-amber-300",
};

interface MarketStateProps {
  phase: MarketPhase;
  sentiment: Sentiment;
  avgDci: number;
  avgConfidence: number;
  trackedSymbols: number;
  activeSignals: number;
  asOf?: string;
}

export function MarketStateView({
  phase,
  sentiment,
  avgDci,
  avgConfidence,
  trackedSymbols,
  activeSignals,
  asOf,
}: MarketStateProps) {
  const phaseStyle = PHASE_STYLES[phase];

  return (
    <Card
      accent
      title="Market State"
      subtitle={asOf ? `as of ${asOf}` : "live"}
      rightSlot={
        <span
          className={classNames(
            "nemt-phase-chip ring-1",
            phaseStyle.cls
          )}
        >
          <span className={classNames("w-1.5 h-1.5 rounded-full", phaseStyle.dot)} />
          {phaseStyle.label}
        </span>
      }
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Sentiment" value={sentiment} valueClass={SENTIMENT_STYLES[sentiment]} />
        <Stat label="Avg DCI" value={avgDci.toFixed(1)} suffix="/100" />
        <Stat label="Avg Confidence" value={`${avgConfidence.toFixed(1)}%`} />
        <Stat
          label="Active Signals"
          value={activeSignals.toString()}
          hint={`${trackedSymbols} symbols tracked`}
        />
      </div>

      <div className="mt-5">
        <DciBar value={avgDci} />
      </div>
    </Card>
  );
}

function Stat({
  label,
  value,
  suffix,
  hint,
  valueClass = "text-slate-100",
}: {
  label: string;
  value: string;
  suffix?: string;
  hint?: string;
  valueClass?: string;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-1">{label}</div>
      <div className={classNames("text-xl font-semibold nemt-mono", valueClass)}>
        {value}
        {suffix && <span className="text-sm text-slate-500 ml-1">{suffix}</span>}
      </div>
      {hint && <div className="text-[11px] text-slate-500 mt-0.5">{hint}</div>}
    </div>
  );
}

function DciBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  // color follows DCI band
  const color =
    pct >= 65 ? "bg-emerald-400" :
    pct >= 50 ? "bg-amber-400" :
    pct >= 35 ? "bg-slate-400" :
                "bg-rose-400";
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
        <span>DCI Composite</span>
        <span className="nemt-mono">{pct.toFixed(1)}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
        <div
          className={classNames("h-full transition-all", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export { formatPercent };
