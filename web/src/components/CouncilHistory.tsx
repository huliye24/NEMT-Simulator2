"use client";

import { useEffect, useState } from "react";
import { Card } from "./Card";
import { Memory, notifyMemoryChanged } from "@/lib/memory";
import { COUNCIL_AGENTS, RECOMMENDATION_LABELS } from "@/lib/council";
import type { CouncilVerdict, Recommendation } from "@/lib/types";
import { classNames, formatRelativeTime } from "@/lib/format";

const REC_TONE: Record<Recommendation, string> = {
  STRONG_BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30",
  BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/20",
  HOLD: "text-slate-300 bg-slate-500/10 ring-slate-500/30",
  REDUCE: "text-amber-300 bg-amber-500/10 ring-amber-500/30",
  SELL: "text-rose-300 bg-rose-500/10 ring-rose-500/30",
  WAIT: "text-slate-300 bg-slate-500/10 ring-slate-500/20",
};

interface CouncilHistoryProps {
  /** Called when the operator wants to inspect a specific verdict. */
  onSelect?: (verdict: CouncilVerdict) => void;
}

/**
 * Persistent council session log. Reads from Financial Memory,
 * survives page reloads, and lets the operator drill into a
 * transcript for audit.
 */
export default function CouncilHistory({ onSelect }: CouncilHistoryProps) {
  const [verdicts, setVerdicts] = useState<CouncilVerdict[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      const all = await Memory.Council.list();
      if (!cancelled) {
        setVerdicts(all);
        setHydrated(true);
      }
    };
    refresh();
    const onChange = () => refresh();
    window.addEventListener("nemt:memory-changed", onChange);
    return () => {
      cancelled = true;
      window.removeEventListener("nemt:memory-changed", onChange);
    };
  }, []);

  const onClear = async () => {
    if (!confirm("Clear all council verdicts from local memory?")) return;
    await Memory.Council.clear();
    setVerdicts([]);
    notifyMemoryChanged();
  };

  return (
    <Card
      title="Council Verdicts"
      subtitle={hydrated ? `${verdicts.length} stored locally` : "loading…"}
      accent
    >
      {!hydrated && (
        <div className="text-[12px] text-slate-500 italic">
          Reading from Financial Memory…
        </div>
      )}

      {hydrated && verdicts.length === 0 && (
        <div className="text-[12px] text-slate-500 italic">
          No council sessions yet. Convene one above to see it logged here.
        </div>
      )}

      {verdicts.length > 0 && (
        <ul className="space-y-3">
          {verdicts.map((v) => (
            <VerdictRow
              key={v.id}
              verdict={v}
              onSelect={onSelect ? () => onSelect(v) : undefined}
            />
          ))}
        </ul>
      )}

      {verdicts.length > 0 && (
        <button
          onClick={onClear}
          className="mt-4 text-[11px] uppercase tracking-wider text-rose-300/80 hover:text-rose-300 transition-colors"
        >
          Clear all verdicts
        </button>
      )}
    </Card>
  );
}

function VerdictRow({
  verdict,
  onSelect,
}: {
  verdict: CouncilVerdict;
  onSelect?: () => void;
}) {
  // Show agent vote distribution as a mini sparkline.
  const distribution = verdict.consensus.distribution;
  const order: Recommendation[] = [
    "STRONG_BUY",
    "BUY",
    "HOLD",
    "REDUCE",
    "SELL",
    "WAIT",
  ];
  const max = Math.max(...Object.values(distribution), 0.01);

  return (
    <li
      className={classNames(
        "bg-slate-900/60 rounded-md p-3 ring-1 ring-slate-800 transition-all",
        onSelect && "cursor-pointer hover:ring-amber-500/30"
      )}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={classNames(
              "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded ring-1",
              REC_TONE[verdict.decision]
            )}
          >
            {RECOMMENDATION_LABELS[verdict.decision]}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            {verdict.outcome.toLowerCase()}
          </span>
          <span className="text-[10px] text-slate-500">
            {formatRelativeTime(verdict.decidedAt)}
          </span>
        </div>
        <span className="nemt-mono text-[11px] text-amber-300">
          {verdict.confidence}%
        </span>
      </div>

      <p className="text-[12px] text-slate-300 line-clamp-2 leading-relaxed">
        {verdict.humanThesis.marketJudgment || "—"}
      </p>

      <div className="mt-3 flex items-center gap-1.5">
        {order.map((rec) => {
          const w = distribution[rec] ?? 0;
          if (w === 0) return null;
          return (
            <div
              key={rec}
              className="h-1.5 rounded-full"
              style={{
                width: `${Math.max(8, (w / max) * 60)}px`,
                backgroundColor:
                  rec === verdict.decision ? "#fbbf24" : "#475569",
              }}
              title={`${RECOMMENDATION_LABELS[rec]}: ${(w * 100).toFixed(1)}%`}
            />
          );
        })}
        <div className="ml-auto flex items-center gap-1">
          {COUNCIL_AGENTS.map((a) => (
            <span
              key={a.id}
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: a.color }}
              title={a.name}
            />
          ))}
        </div>
      </div>
    </li>
  );
}
