import { Card } from "@/components/Card";
import { MarketCard } from "@/components/MarketCard";
import { getMarketSymbols, getMarketState } from "@/lib/api";
import { classNames, formatPercent } from "@/lib/format";

export default async function MarketPage() {
  const [symbols, state] = await Promise.all([getMarketSymbols(), getMarketState()]);

  // Build a quick aggregate by phase
  const byPhase = symbols.reduce<Record<string, number>>((acc, s) => {
    acc[s.phase] = (acc[s.phase] ?? 0) + 1;
    return acc;
  }, {});

  const totalChange = symbols.reduce((sum, s) => sum + s.change24h, 0) / symbols.length;
  const gainers = symbols.filter((s) => s.change24h > 0).length;
  const losers = symbols.filter((s) => s.change24h < 0).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">Market</div>
        <h1 className="text-2xl font-bold text-slate-100">Live Market Overview</h1>
        <p className="text-sm text-slate-400 mt-1">
          All tracked symbols with phase, DCI, and confidence. Read-only mock data.
        </p>
      </header>

      {/* Aggregates */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Market Phase" value={state.phase} accent="amber" />
        <Kpi
          label="Avg 24h Change"
          value={formatPercent(totalChange)}
          tone={totalChange >= 0 ? "up" : "down"}
        />
        <Kpi label="Gainers / Losers" value={`${gainers} / ${losers}`} />
        <Kpi label="Tracked" value={symbols.length.toString()} />
      </div>

      {/* Phase distribution */}
      <Card title="Phase Distribution" subtitle="how many symbols are in each phase">
        <div className="flex flex-wrap gap-3">
          {Object.entries(byPhase).map(([phase, count]) => (
            <div
              key={phase}
              className="flex items-center gap-2 px-3 py-2 rounded-md bg-nemt-bg-elevated/60 ring-1 ring-amber-500/10"
            >
              <span className="text-[10px] uppercase tracking-wider text-slate-400">
                {phase}
              </span>
              <span className="text-sm font-semibold nemt-mono text-amber-300">
                {count}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* Symbol grid */}
      <section>
        <div className="flex items-end justify-between mb-3">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
            All Symbols
          </h2>
          <span className="text-[11px] text-slate-500">{symbols.length} total</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {symbols.map((s) => (
            <MarketCard key={s.symbol} symbol={s} />
          ))}
        </div>
      </section>
    </div>
  );
}

function Kpi({
  label,
  value,
  tone = "neutral",
  accent,
}: {
  label: string;
  value: string;
  tone?: "up" | "down" | "neutral";
  accent?: "amber";
}) {
  const toneCls =
    tone === "up" ? "text-emerald-300" :
    tone === "down" ? "text-rose-300" :
    accent === "amber" ? "nemt-amber-text" :
    "text-slate-100";
  return (
    <div className="nemt-panel p-4">
      <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-1">
        {label}
      </div>
      <div className={classNames("text-xl font-semibold nemt-mono", toneCls)}>
        {value}
      </div>
    </div>
  );
}
