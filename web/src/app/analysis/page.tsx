import AnalysisConsole from "@/components/AnalysisConsole";
import { getAnalyses, getMarketState } from "@/lib/api";
import type { MarketContext } from "@/lib/types";


export default async function AnalysisPage() {
  const [analyses, marketState] = await Promise.all([
    getAnalyses(),
    getMarketState(),
  ]);

  const dominantSymbol = analyses[0]?.marketContext.dominantSymbol ?? "BTCUSDT";

  const marketContext: MarketContext = {
    phase: marketState.phase,
    dominantSymbol,
    avgDci: marketState.avgDci,
    sentiment: marketState.sentiment,
    keyLevels: {
      support: 65_000,
      resistance: 70_000,
    },
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">
          Analysis
        </div>
        <h1 className="text-2xl font-bold text-slate-100">AI Reasoning Layer</h1>
        <p className="text-sm text-slate-400 mt-1">
          Human thesis meets the council. Each decision is committed to the
          Financial Memory and replayed here.
        </p>
      </header>

      <AnalysisConsole
        initialAnalyses={analyses}
        marketContext={marketContext}
      />
    </div>
  );
}
