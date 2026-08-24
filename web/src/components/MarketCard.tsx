"use client";

import { Card } from "./Card";
import type { MarketSymbol, MarketPhase } from "@/lib/types";
import { classNames, dciColor, formatPercent, formatPrice, formatUsd } from "@/lib/format";

const PHASE_DOT: Record<MarketPhase, string> = {
  ACCUMULATION: "bg-blue-400",
  MARKUP: "bg-emerald-400",
  DISTRIBUTION: "bg-amber-400",
  MARKDOWN: "bg-rose-400",
  RECOVERY: "bg-cyan-400",
  UNKNOWN: "bg-slate-400",
};

interface MarketCardProps {
  symbol: MarketSymbol;
}

export function MarketCard({ symbol }: MarketCardProps) {
  const isUp = symbol.change24h >= 0;
  const dciBand = dciColor(symbol.dci.value);

  return (
    <div
      className={classNames(
        "nemt-panel w-full p-4 transition-all",
        "hover:border-amber-500/40 hover:translate-y-[-1px]"
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-[15px] font-semibold text-slate-100 nemt-mono">
            {symbol.display}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={classNames("w-1.5 h-1.5 rounded-full", PHASE_DOT[symbol.phase])} />
            <span className="text-[10px] uppercase tracking-wider text-slate-400">
              {symbol.phase}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[15px] font-semibold nemt-mono text-slate-100">
            {formatPrice(symbol.price)}
          </div>
          <div
            className={classNames(
              "text-[12px] nemt-mono font-medium",
              isUp ? "nemt-up" : "nemt-down"
            )}
          >
            {formatPercent(symbol.change24h)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 pt-3 border-t nemt-divider">
        <Mini label="DCI" value={symbol.dci.value.toFixed(1)} tone={dciBand} />
        <Mini label="Conf" value={`${symbol.confidence.toFixed(0)}%`} />
        <Mini label="24h Vol" value={formatUsd(symbol.volume24h, { compact: true })} />
      </div>
    </div>
  );
}

function Mini({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "up" | "down" | "warn" | "neutral";
}) {
  const toneCls =
    tone === "up" ? "text-emerald-300" :
    tone === "down" ? "text-rose-300" :
    tone === "warn" ? "text-amber-300" :
    "text-slate-200";
  return (
    <div>
      <div className="text-[9px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={classNames("text-[12px] nemt-mono font-medium mt-0.5", toneCls)}>
        {value}
      </div>
    </div>
  );
}
