"use client";

import { useState } from "react";

interface HumanThesisInputProps {
  onSubmit?: (thesis: {
    macroView: string;
    marketJudgment: string;
    riskFactors: string;
    actionPlan: string;
  }) => void;
}

export default function HumanThesisInput({ onSubmit }: HumanThesisInputProps) {
  const [macroView, setMacroView] = useState("");
  const [marketJudgment, setMarketJudgment] = useState("");
  const [riskFactors, setRiskFactors] = useState("");
  const [actionPlan, setActionPlan] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!macroView || !marketJudgment) return;

    setIsSubmitting(true);

    // Simulate AI processing
    await new Promise((r) => setTimeout(r, 1500));

    onSubmit?.({
      macroView,
      marketJudgment,
      riskFactors,
      actionPlan,
    });

    setIsSubmitting(false);
  };

  const isValid = macroView && marketJudgment;

  return (
    <div className="nemt-panel p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="w-2 h-2 bg-amber-400 rounded-full" />
        <h2 className="text-lg font-semibold text-white">Human Thesis</h2>
        <span className="text-xs text-slate-500 ml-2">Input your market view</span>
      </div>

      <div className="space-y-4">
        {/* Macro View */}
    <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
            Macro View <span className="text-amber-400">*</span>
          </label>
          <textarea
            value={macroView}
            onChange={(e) => setMacroView(e.target.value)}
            placeholder="e.g., Fed rate cut expectations rising, liquidity improving..."
            className="w-full bg-nemt-bg-deep border border-nemt-border rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 min-h-[80px] resize-none"
          />
        </div>

        {/* Market Judgment */}
        <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
            Market Judgment <span className="text-amber-400">*</span>
          </label>
          <textarea
            value={marketJudgment}
            onChange={(e) => setMarketJudgment(e.target.value)}
            placeholder="e.g., BTC breaking key resistance, trend turning bullish..."
            className="w-full bg-nemt-bg-deep border border-nemt-border rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 min-h-[80px] resize-none"
          />
        </div>

        {/* Risk Factors */}
        <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
            Risk Factors
          </label>
          <textarea
            value={riskFactors}
            onChange={(e) => setRiskFactors(e.target.value)}
            placeholder="e.g., Short-term overbought, potential pullback..."
            className="w-full bg-nemt-bg-deep border border-nemt-border rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 min-h-[60px] resize-none"
          />
        </div>

        {/* Action Plan */}
        <div>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
            Action Plan
          </label>
          <textarea
            value={actionPlan}
            onChange={(e) => setActionPlan(e.target.value)}
            placeholder="e.g., Scale in gradually, set stop loss at..."
            className="w-full bg-nemt-bg-deep border border-nemt-border rounded-lg px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 min-h-[60px] resize-none"
          />
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={!isValid || isSubmitting}
          className="w-full py-3 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed
            bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-white"
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              AI Processing...
            </span>
          ) : (
            "Generate AI Analysis"
          )}
        </button>
      </div>
    </div>
  );
}
