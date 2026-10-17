import Link from "next/link";
import { Card } from "@/components/Card";
import { MarketStateView } from "@/components/MarketState";
import { PortfolioView } from "@/components/Portfolio";
import { getMarketState, getMarketSymbols, getPortfolio, getOpenTrades, getLatestReport } from "@/lib/api";
import { getSystemState } from "@/lib/api";
import { classNames } from "@/lib/format";
import type { MarketSymbol } from "@/lib/types";

export default async function FinancialOSPage() {
  const [marketState, symbols, portfolio, trades, latestReport, systemState] = await Promise.all([
    getMarketState(),
    getMarketSymbols(),
    getPortfolio(),
    getOpenTrades(),
    getLatestReport(),
    getSystemState(),
  ]);

  const featuredSymbols = symbols.slice(0, 4);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <header>
        <div className="flex items-center gap-3">
          <span className="nemt-phase-chip text-amber-300 bg-amber-500/10 ring-1 ring-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Financial OS v1.0
          </span>
          <span className="text-[11px] uppercase tracking-wider text-slate-500">
            NEMT · AI Financial Intelligence
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-100 mt-2">
          NEMT Financial OS
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl mt-1">
          Human Intelligence + AI Financial Agents + Market Physics Engine + Execution Infrastructure
        </p>
      </header>

      {/* System Status Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <SystemStatusCard
          title="Market"
          status={systemState.modules.market.status}
          value={`${systemState.marketState.trackedSymbols} symbols`}
        />
        <SystemStatusCard
          title="AI Council"
          status={systemState.modules.aiCouncil.status}
          value={`${systemState.modules.aiCouncil.agents} agents`}
        />
        <SystemStatusCard
          title="Trading"
          status={systemState.modules.trading.status}
          value={systemState.modules.trading.mode ?? "—"}
        />
        <SystemStatusCard
          title="Engine"
          status={systemState.modules.engine.status}
          value={`v${systemState.modules.engine.version}`}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Market & AI */}
        <div className="lg:col-span-2 space-y-6">
          {/* Market State */}
          <MarketStateView
            phase={marketState.phase}
            sentiment={marketState.sentiment}
            avgDci={marketState.avgDci}
            avgConfidence={marketState.avgConfidence}
            trackedSymbols={marketState.trackedSymbols}
            activeSignals={marketState.activeSignals}
            asOf={marketState.asOf}
          />

          {/* Featured Markets */}
          <section>
            <SectionHeader
              title="Featured Markets"
              hint={`${symbols.length} symbols tracked`}
              cta={{ href: "/market", label: "View all" }}
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {featuredSymbols.map((s) => (
                <MarketCard key={s.symbol} symbol={s} />
              ))}
            </div>
          </section>

          {/* AI Council Preview */}
          {latestReport && (
            <Card
              accent
              title={
                <div className="flex items-center gap-2">
                  <span className="text-amber-300">●</span>
                  <span>AI Council Verdict</span>
                </div>
              }
              subtitle={latestReport.title}
              rightSlot={
                <span className={classNames(
                  "nemt-phase-chip ring-1",
                  "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30"
                )}>
                  {latestReport.recommendation}
                </span>
              }
            >
              <p className="text-sm text-slate-200 leading-relaxed mb-4">
                {latestReport.summary}
              </p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-slate-500">Confidence:</span>
                <span className="text-blue-400 font-mono">{latestReport.confidence.toFixed(1)}%</span>
                <span className="text-slate-500">DCI:</span>
                <span className="text-amber-400 font-mono">{latestReport.dci.toFixed(1)}</span>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column - Portfolio & Memory */}
        <div className="space-y-6">
          {/* Portfolio */}
          <PortfolioView portfolio={portfolio} />

          {/* Quick Stats */}
          <Card title="System Overview" subtitle="NEMT Financial OS v1.0">
            <div className="space-y-3">
              <StatRow label="Portfolio P&L" value={`+$${portfolio.pnl.toFixed(2)}`} valueClass="text-emerald-400" />
              <StatRow label="Open Trades" value={`${trades.length}`} />
              <StatRow label="Memory Records" value={`${systemState.memory.totalDecisions}`} />
              <StatRow label="Daily Loss" value={`-$${systemState.risk.dailyLoss.toFixed(2)} / $${systemState.risk.dailyLossLimit}`} valueClass="text-slate-400" />
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2">
                <div className={classNames(
                  "w-2 h-2 rounded-full",
                  systemState.risk.emergencyStop ? "bg-red-500" : "bg-emerald-500"
                )} />
                <span className="text-sm text-slate-400">
                  {systemState.risk.emergencyStop ? "Emergency Stop Active" : "System Normal"}
                </span>
              </div>
            </div>
          </Card>

          {/* Quick Links */}
          <Card title="Navigation" subtitle="Quick access">
            <div className="grid grid-cols-2 gap-2">
              <QuickLink href="/market" label="Market" />
              <QuickLink href="/analysis" label="Analysis" />
              <QuickLink href="/simulation" label="Simulation" />
              <QuickLink href="/journal" label="Journal" />
              <QuickLink href="/settings" label="Settings" />
              <QuickLink href="/system" label="System" />
            </div>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 pt-6 mt-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            <span className="text-amber-400 font-semibold">NEMT</span>
            <span className="ml-2">Financial OS v1.0</span>
            <span className="ml-2 text-slate-600">·</span>
            <span className="ml-2">{systemState.modules.engine.version}</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Started: {new Date(systemState.startedAt).toLocaleDateString()}</span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              All systems operational
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Components
function SystemStatusCard({ title, status, value }: { title: string; status: string; value: string }) {
  const statusColors: Record<string, string> = {
    healthy: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-red-500",
  };

  return (
    <div className="nemt-panel p-3">
      <div className="flex items-center gap-2">
        <span className={classNames("w-2 h-2 rounded-full", statusColors[status] || "bg-slate-500")} />
        <span className="text-xs text-slate-500 uppercase tracking-wider">{title}</span>
      </div>
      <div className="text-sm font-semibold text-slate-100 mt-1">{value}</div>
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

function MarketCard({ symbol }: { symbol: MarketSymbol }) {
  const isPositive = symbol.change24h >= 0;

  return (
    <div className="nemt-panel p-4 hover:border-amber-500/30 transition-all">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-slate-100">{symbol.display}</span>
        <span className={classNames(
          "text-xs px-2 py-0.5 rounded",
          symbol.phase === "MARKUP" ? "bg-emerald-500/10 text-emerald-400" :
          symbol.phase === "ACCUMULATION" ? "bg-blue-500/10 text-blue-400" :
          symbol.phase === "DISTRIBUTION" ? "bg-amber-500/10 text-amber-400" :
          "bg-rose-500/10 text-rose-400"
        )}>
          {symbol.phase}
        </span>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <span className="text-lg font-mono font-semibold text-slate-100">
            ${symbol.price.toLocaleString()}
          </span>
          <span className={classNames(
            "text-xs ml-2",
            isPositive ? "text-emerald-400" : "text-rose-400"
          )}>
            {isPositive ? "+" : ""}{symbol.change24h.toFixed(2)}%
          </span>
        </div>
        <div className="text-xs text-slate-500">
          DCI: <span className="text-amber-400">{symbol.dci.value}</span>
        </div>
      </div>
    </div>
  );
}

function StatRow({ label, value, valueClass = "text-slate-100" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={classNames("text-sm font-medium", valueClass)}>{value}</span>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="text-center py-2 px-3 rounded bg-nemt-bg-deep border border-nemt-border hover:border-amber-500/30 transition-all text-sm text-slate-300 hover:text-slate-100"
    >
      {label}
    </Link>
  );
}
