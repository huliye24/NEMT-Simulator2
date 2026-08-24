"use client";

import type { AIReport } from "@/lib/types";
import PhaseIndicator from "./PhaseIndicator";

interface AIReportCardProps {
  report: AIReport;
}

const recommendationColors: Record<string, string> = {
  STRONG_BUY: "text-emerald-400 border-emerald-500/50 bg-emerald-500/10",
  BUY: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  HOLD: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  REDUCE: "text-orange-400 border-orange-500/30 bg-orange-500/10",
  SELL: "text-red-400 border-red-500/30 bg-red-500/10",
  WAIT: "text-slate-400 border-slate-500/30 bg-slate-500/10",
};

export default function AIReportCard({ report }: AIReportCardProps) {
  const recStyle = recommendationColors[report.recommendation] || recommendationColors.WAIT;

  return (
    <div className="nemt-panel p-5 hover:border-amber-500/40 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">{report.title}</h3>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span className="font-mono">{report.symbol}</span>
            <span>•</span>
            <PhaseIndicator phase={report.phase} size="sm" />
            <span>•</span>
            <span>{new Date(report.generatedAt).toLocaleString()}</span>
          </div>
        </div>
        <div
          className={`px-3 py-1.5 rounded-lg border font-bold text-sm ${recStyle}`}
        >
          {report.recommendation}
        </div>
      </div>

      {/* Summary */}
      <div className="mb-4">
        <p className="text-slate-300 leading-relaxed">{report.summary}</p>
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-4 mb-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">DCI</span>
          <span className="font-mono font-bold text-amber-400">{report.dci.toFixed(1)}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">CONFIDENCE</span>
          <span className="font-mono font-bold text-blue-400">{report.confidence.toFixed(1)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">BY</span>
          <span className="text-slate-300">{report.author}</span>
        </div>
      </div>

      {/* Reasoning */}
      <div>
        <span className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">
          Reasoning
        </span>
        <ul className="space-y-2">
          {report.reasoning.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-slate-400">
              <span className="text-amber-500 mt-0.5">›</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
