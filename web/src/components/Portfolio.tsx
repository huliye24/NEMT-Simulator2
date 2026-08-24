import { Card } from "./Card";
import type { Portfolio, PortfolioPosition } from "@/lib/types";
import { classNames, formatPercent, formatPrice, formatUsd } from "@/lib/format";

interface PortfolioViewProps {
  portfolio: Portfolio;
}

export function PortfolioView({ portfolio }: PortfolioViewProps) {
  const isUp = portfolio.pnl >= 0;
  return (
    <Card
      accent
      title="Portfolio"
      subtitle={`Starting capital ${formatUsd(portfolio.startingCapital)}`}
      rightSlot={
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Equity</div>
          <div className="text-base font-semibold nemt-mono text-slate-100">
            {formatUsd(portfolio.equity)}
          </div>
        </div>
      }
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <Stat label="Capital" value={formatUsd(portfolio.capital)} />
        <Stat
          label="P/L"
          value={formatUsd(portfolio.pnl)}
          tone={isUp ? "up" : "down"}
        />
        <Stat
          label="P/L %"
          value={formatPercent(portfolio.pnlPct)}
          tone={isUp ? "up" : "down"}
        />
        <Stat label="Positions" value={portfolio.positions.length.toString()} />
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-2">
          Open Positions
        </div>
        <div className="overflow-x-auto -mx-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-slate-500">
                <th className="text-left font-medium px-2 py-2">Symbol</th>
                <th className="text-left font-medium px-2 py-2">Side</th>
                <th className="text-right font-medium px-2 py-2">Size</th>
                <th className="text-right font-medium px-2 py-2">Entry</th>
                <th className="text-right font-medium px-2 py-2">Mark</th>
                <th className="text-right font-medium px-2 py-2">P/L</th>
                <th className="text-right font-medium px-2 py-2">P/L %</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((p) => (
                <PositionRow key={p.symbol} position={p} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}

function PositionRow({ position }: { position: PortfolioPosition }) {
  const isUp = position.pnl >= 0;
  return (
    <tr className="border-t nemt-divider hover:bg-nemt-bg-hover/40 transition-colors">
      <td className="px-2 py-2.5 nemt-mono font-medium text-slate-100">{position.symbol}</td>
      <td className="px-2 py-2.5">
        <span
          className={classNames(
            "text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded",
            position.side === "LONG"
              ? "bg-emerald-500/10 text-emerald-300"
              : "bg-rose-500/10 text-rose-300"
          )}
        >
          {position.side}
        </span>
      </td>
      <td className="px-2 py-2.5 text-right nemt-mono text-slate-200">
        {position.size.toLocaleString("en-US", { maximumFractionDigits: 4 })}
      </td>
      <td className="px-2 py-2.5 text-right nemt-mono text-slate-300">
        {formatPrice(position.entry)}
      </td>
      <td className="px-2 py-2.5 text-right nemt-mono text-slate-100">
        {formatPrice(position.mark)}
      </td>
      <td
        className={classNames(
          "px-2 py-2.5 text-right nemt-mono font-medium",
          isUp ? "nemt-up" : "nemt-down"
        )}
      >
        {formatUsd(position.pnl)}
      </td>
      <td
        className={classNames(
          "px-2 py-2.5 text-right nemt-mono font-medium",
          isUp ? "nemt-up" : "nemt-down"
        )}
      >
        {formatPercent(position.pnlPct)}
      </td>
    </tr>
  );
}

function Stat({
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
    <div>
      <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-1">{label}</div>
      <div className={classNames("text-base font-semibold nemt-mono", toneCls)}>{value}</div>
    </div>
  );
}
