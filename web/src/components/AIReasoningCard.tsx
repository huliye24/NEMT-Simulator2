"use client";

import type { AIReasoning, MarketContext } from "@/lib/types";
import { classNames } from "@/lib/format";

interface AIReasoningCardProps {
  reasoning: AIReasoning;
  marketContext: MarketContext;
}

const REC_STYLES: Record<string, string> = {
  STRONG_BUY: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50",
  BUY: "bg-emerald-500/15 text-emerald-400 border-emerald-500/40",
  HOLD: "bg-slate-500/20 text-slate-300 border-slate-500/40",
  REDUCE: "bg-amber-500/20 text-amber-400 border-amber-500/50",
  SELL: "bg-rose-500/20 text-rose-400 border-rose-500/50",
  WAIT: "bg-blue-500/20 text-blue-400 border-blue-500/40",
};

const RISK_STYLES: Record<string, string> = {
  LOW: "text-emerald-400",
  MEDIUM: "text-amber-400",
  HIGH: "text-rose-400",
};

export default function AIReasoningCard({ reasoning, marketContext }: AIReasoningCardProps) {
  return (
    <div className="nemt-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
        <h2 className="text-lg font-semibold text-white">AI Reasoning</h2>
        <span className="text-xs text-slate-500 ml-2">NEMT Council Analysis</span>
      </div>

      <div className="space-y-6">
        {/* Market Interpretation */}
        <div className="bg-nemt-bg-deep rounded-lg p-4 border border-nemt-border">
          <span className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">
            Market Interpretation
          </span>
          <p className="text-slate-200 text-sm leading-relaxed">
            {reasoning.marketInterpretation}
          </p>
        </div>

        {/* Market Context Summary */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-nemt-bg-deep rounded-lg p-3 border border-nemt-border">
            <span className="text-xs text-slate-500 block mb-1">Phase</span>
            <span className={classNames(
              "text-sm font-semibold",
              marketContext.phase === "MARKUP" ? "text-emerald-400" :
              marketContext.phase === "ACCUMULATION" ? "text-blue-400" :
              marketContext.phase === "DISTRIBUTION" ? "text-amber-400" :
              marketContext.phase === "MARKDOWN" ? "text-rose-400" :
              "text-cyan-400"
            )}>
              {marketContext.phase}
            </span>
          </div>
          <div className="bg-nemt-bg-deep rounded-lg p-3 border border-nemt-border">
            <span className="text-xs text-slate-500 block mb-1">DCI</span>
            <span className="text-sm font-semibold text-amber-400">
              {marketContext.avgDci.toFixed(1)}
            </span>
          </div>
          <div className="bg-nemt-bg-deep rounded-lg p-3 border border-nemt-border">
            <span className="text-xs text-slate-500 block mb-1">Sentiment</span>
            <span className={classNames(
              "text-sm font-semibold",
              marketContext.sentiment === "BULLISH" ? "text-emerald-400" :
              marketContext.sentiment === "BEARISH" ? "text-rose-400" :
              marketContext.sentiment === "CAUTIOUS" ? "text-amber-400" :
              "text-slate-300"
            )}>
              {marketContext.sentiment}
            </span>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="bg-nemt-bg-deep rounded-lg p-4 border border-nemt-border">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs text-slate-500 uppercase tracking-wider">
              Risk Assessment
            </span>
            <span className={classNames(
              "text-xs font-semibold px-2 py-0.5 rounded",
              RISK_STYLES[reasoning.riskAssessment.level]
            )}>
              {reasoning.riskAssessment.level}
            </span>
          </div>
          <ul className="space-y-1">
            {reasoning.riskAssessment.factors.map((factor, idx) => (
              <li key={idx} className="text-sm text-slate-400 flex items-start gap-2">
                <span className="text-rose-400 mt-0.5">⚠</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendation */}
        <div className="flex items-center justify-between bg-nemt-bg-deep rounded-lg p-4 border border-nemt-border">
          <div>
            <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">
              Recommendation
            </span>
            <span className={classNames(
              "text-2xl font-bold px-4 py-2 rounded-lg border",
              REC_STYLES[reasoning.recommendation] || REC_STYLES.WAIT
            )}>
              {reasoning.recommendation}
            </span>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">
              Confidence
            </span>
            <span className="text-2xl font-bold text-blue-400">
              {reasoning.confidence.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Reasoning Chain */}
        <div>
          <span className="text-xs text-slate-500 uppercase tracking-wider mb-3 block">
            Reasoning Chain
          </span>
          <div className="space-y-2">
            {reasoning.reasoning.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-xs font-mono">
                  {idx + 1}
                </span>
                <span className="text-sm text-slate-300 flex-1">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
