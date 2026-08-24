import { Card } from "@/components/Card";
import { PortfolioView } from "@/components/Portfolio";
import { getPortfolio, getTrades } from "@/lib/api";
import { classNames, formatPercent, formatRelativeTime, formatUsd } from "@/lib/format";

export default async function SimulationPage() {
  const [portfolio, trades] = await Promise.all([getPortfolio(), getTrades()]);

  const closed = trades.filter((t) => t.status === "CLOSED");
  const open = trades.filter((t) => t.status === "OPEN");
  const wins = closed.filter((t) => (t.pnl ?? 0) > 0);
  const losses = closed.filter((t) => (t.pnl ?? 0) <= 0);
  const winRate = closed.length > 0 ? (wins.length / closed.length) * 100 : 0;
  const totalPnl = closed.reduce((s, t) => s + (t.pnl ?? 0), 0);
  const avgWin = wins.length > 0 ? wins.reduce((s, t) => s + (t.pnl ?? 0), 0) / wins.length : 0;
  const avgLoss = losses.length > 0 ? losses.reduce((s, t) => s + (t.pnl ?? 0), 0) / losses.length : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">Simulation</div>
        <h1 className="text-2xl font-bold text-slate-100">Paper Trading Console</h1>
        <p className="text-sm text-slate-400 mt-1">
          Paper-only ledger. No live execution. All numbers are derived from the mock trade book.
        </p>
      </header>

      {/* Performance KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Win Rate" value={`${winRate.toFixed(1)}%`} />
        <Kpi
          label="Realized P/L"
          value={formatUsd(totalPnl)}
          tone={totalPnl >= 0 ? "up" : "down"}
        />
        <Kpi label="Avg Win" value={formatUsd(avgWin)} tone="up" />
        <Kpi label="Avg Loss" value={formatUsd(avgLoss)} tone="down" />
      </div>

      {/* Portfolio */}
      <PortfolioView portfolio={portfolio} />

      {/* Trade book */}
      <Card title="Trade Book" subtitle={`${open.length} open · ${closed.length} closed`}>
        <div className="overflow-x-auto -mx-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-slate-500">
                <th className="text-left font-medium px-2 py-2">Opened</th>
                <th className="text-left font-medium px-2 py-2">Symbol</th>
                <th className="text-left font-medium px-2 py-2">Side</th>
                <th className="text-right font-medium px-2 py-2">Entry</th>
                <th className="text-right font-medium px-2 py-2">Exit</th>
                <th className="text-right font-medium px-2 py-2">Size</th>
                <th className="text-right font-medium px-2 py-2">P/L</th>
                <th className="text-left font-medium px-2 py-2">Status</th>
                <th className="text-left font-medium px-2 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => {
                const isWin = (t.pnl ?? 0) > 0;
                return (
                  <tr key={t.id} className="border-t nemt-divider hover:bg-nemt-bg-hover/40">
                    <td className="px-2 py-2.5 text-[12px] text-slate-400">
                      {formatRelativeTime(t.openedAt)}
                    </td>
                    <td className="px-2 py-2.5 nemt-mono font-medium text-slate-100">{t.symbol}</td>
                    <td className="px-2 py-2.5">
                      <span
                        className={classNames(
                          "text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded",
                          t.side === "LONG"
                            ? "bg-emerald-500/10 text-emerald-300"
                            : "bg-rose-500/10 text-rose-300"
                        )}
                      >
                        {t.side}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-right nemt-mono text-slate-300">
                      {t.entry.toLocaleString("en-US", { maximumFractionDigits: 4 })}
                    </td>
                    <td className="px-2 py-2.5 text-right nemt-mono text-slate-400">
                      {t.exit ? t.exit.toLocaleString("en-US", { maximumFractionDigits: 4 }) : "—"}
                    </td>
                    <td className="px-2 py-2.5 text-right nemt-mono text-slate-300">
                      {t.size}
                    </td>
                    <td
                      className={classNames(
                        "px-2 py-2.5 text-right nemt-mono font-medium",
                        t.status === "OPEN"
                          ? "text-slate-400"
                          : isWin
                          ? "nemt-up"
                          : "nemt-down"
                      )}
                    >
                      {t.status === "OPEN"
                        ? "—"
                        : `${formatUsd(t.pnl ?? 0)} (${formatPercent(t.pnlPct ?? 0)})`}
                    </td>
                    <td className="px-2 py-2.5">
                      <span
                        className={classNames(
                          "text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded",
                          t.status === "OPEN"
                            ? "bg-blue-500/10 text-blue-300"
                            : "bg-slate-500/10 text-slate-300"
                        )}
                      >
                        {t.status}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-[12px] text-slate-400 max-w-xs truncate">
                      {t.reason}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Kpi({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "up" | "down" | "neutral";
}) {
  const toneCls =
    tone === "up" ? "text-emerald-300" :
    tone === "down" ? "text-rose-300" :
    "text-slate-100";
  return (
    <div className="nemt-panel p-4">
      <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-1">{label}</div>
      <div className={classNames("text-xl font-semibold nemt-mono", toneCls)}>{value}</div>
    </div>
  );
}
