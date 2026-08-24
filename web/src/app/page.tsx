import Link from "next/link";
import { MarketStateView } from "@/components/MarketState";
import { MarketCard } from "@/components/MarketCard";
import { AIReportCard } from "@/components/AIReport";
import { PortfolioView } from "@/components/Portfolio";
import {
  getMarketState,
  getMarketSymbols,
  getLatestReport,
  getPortfolio,
  getOpenTrades,
} from "@/lib/api";


export default async function DashboardPage() {
  const [state, symbols, latestReport, portfolio, openTrades] = await Promise.all([
    getMarketState(),
    getMarketSymbols(),
    getLatestReport(),
    getPortfolio(),
    getOpenTrades(),
  ]);

  const featured = symbols.slice(0, 4);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Hero */}
      <section className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <span className="nemt-phase-chip text-amber-300 bg-amber-500/10 ring-1 ring-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Alpha Build
          </span>
          <span className="text-[11px] uppercase tracking-wider text-slate-500">
            NEMT · Financial Intelligence
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-100 mt-2">
          Human Judgment <span className="nemt-amber-text">+</span> AI Execution
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl mt-1">
          A multi-agent system that reads market structure, reasons about phase and confidence,
          and surfaces only the trades worth your attention.
        </p>
      </section>

      {/* Market State */}
      <MarketStateView
        phase={state.phase}
        sentiment={state.sentiment}
        avgDci={state.avgDci}
        avgConfidence={state.avgConfidence}
        trackedSymbols={state.trackedSymbols}
        activeSignals={state.activeSignals}
        asOf={state.asOf}
      />

      {/* Featured Symbols */}
      <section>
        <SectionHeader
          title="Featured Markets"
          hint={`${symbols.length} symbols tracked`}
          cta={{ href: "/market", label: "View all" }}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {featured.map((s) => (
            <MarketCard key={s.symbol} symbol={s} />
          ))}
        </div>
      </section>

      {/* Two-column: AI Report + Portfolio */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <SectionHeader
            title="Latest AI Reasoning"
            cta={{ href: "/analysis", label: "All reports" }}
          />
          {latestReport && <AIReportCard report={latestReport} />}
        </div>
        <div className="lg:col-span-2 space-y-4">
          <SectionHeader
            title="Quick Stats"
            hint={`${openTrades.length} open trades`}
            cta={{ href: "/simulation", label: "Simulation" }}
          />
          <PortfolioView portfolio={portfolio} />
        </div>
      </div>
    </div>
  );
}

function SectionHeader({
  title,
  hint,
  cta,
}: {
  title: string;
  hint?: string;
  cta?: { href: string; label: string };
}) {
  return (
    <div className="flex items-end justify-between mb-3">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
          {title}
        </h2>
        {hint && <p className="text-[11px] text-slate-500 mt-0.5">{hint}</p>}
      </div>
      {cta && (
        <Link
          href={cta.href}
          className="text-[11px] uppercase tracking-wider text-amber-400 hover:text-amber-300 transition-colors"
        >
          {cta.label} →
        </Link>
      )}
    </div>
  );
}
