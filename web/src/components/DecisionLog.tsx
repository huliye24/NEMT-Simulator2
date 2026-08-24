"use client";

import type { Analysis } from "@/lib/types";
import { classNames, formatUsd } from "@/lib/format";

interface DecisionLogProps {
  analyses: Analysis[];
}

const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  CLOSED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  SKIPPED: "bg-slate-500/10 text-slate-400 border-slate-500/30",
};

const ACTION_STYLES: Record<string, string> = {
  BUY: "text-emerald-400",
  SELL: "text-rose-400",
  HOLD: "text-slate-300",
  WAIT: "text-blue-400",
};

export default function DecisionLog({ analyses }: DecisionLogProps) {
  return (
    <div className="nemt-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="w-2 h-2 bg-emerald-400 rounded-full" />
        <h2 className="text-lg font-semibold text-white">Decision Log</h2>
        <span className="text-xs text-slate-500 ml-2">{analyses.length} records</span>
      </div>

      <div className="space-y-4">
        {analyses.map((analysis) => (
          <div
            key={analysis.id}
            className="bg-nemt-bg-deep rounded-lg p-4 border border-nemt-border hover:border-amber-500/30 transition-all"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500 font-mono">
                  {new Date(analysis.date).toLocaleDateString()}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(analysis.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <span className={classNames(
                "text-xs px-2 py-0.5 rounded border",
                STATUS_STYLES[analysis.result.status]
              )}>
                {analysis.result.status}
              </span>
            </div>

            {/* Content */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Human Thesis */}
              <div>
                <span className="text-xs text-slate-500 uppercase tracking-wider mb-1 block">
                  Human Thesis
                </span>
                <p className="text-sm text-slate-300 line-clamp-2">
                  {analysis.humanThesis.marketJudgment}
                </p>
              </div>

              {/* AI Decision */}
              <div>
                <span className="text-xs text-slate-500 uppercase tracking-wider mb-1 block">
                  AI Decision
                </span>
                <div className="flex items-center gap-3">
                  <span className={classNames(
                    "text-sm font-semibold",
                    ACTION_STYLES[analysis.finalDecision.action] || "text-slate-300"
                  )}>
                    {analysis.finalDecision.action}
                  </span>
                  {analysis.finalDecision.size && (
                    <span className="text-xs text-slate-400">
                      {analysis.finalDecision.size}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Result */}
            {analysis.result.status === "CLOSED" && analysis.result.pnl !== null && (
              <div className="mt-3 pt-3 border-t border-nemt-border flex items-center justify-between">
                <span className="text-xs text-slate-500">Result</span>
                <span className={classNames(
                  "text-sm font-mono font-semibold",
                  analysis.result.pnl > 0 ? "text-emerald-400" : "text-rose-400"
                )}>
                  {analysis.result.pnl > 0 ? "+" : ""}
                  {analysis.result.pnl.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
