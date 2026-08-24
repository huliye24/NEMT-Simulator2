import { AIReportCard } from "@/components/AIReport";
import { Card } from "@/components/Card";
import { getReports, getMarketSymbols } from "@/lib/api";
import { classNames } from "@/lib/format";
import type { Recommendation } from "@/lib/types";


const REC_LABEL: Record<Recommendation, string> = {
  STRONG_BUY: "Strong Buy",
  BUY: "Buy",
  HOLD: "Hold",
  REDUCE: "Reduce",
  SELL: "Sell",
  WAIT: "Wait",
};

const REC_TONE: Record<Recommendation, string> = {
  STRONG_BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30",
  BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/20",
  HOLD: "text-slate-300 bg-slate-500/10 ring-slate-500/30",
  REDUCE: "text-amber-300 bg-amber-500/10 ring-amber-500/30",
  SELL: "text-rose-300 bg-rose-500/10 ring-rose-500/30",
  WAIT: "text-slate-300 bg-slate-500/10 ring-slate-500/20",
};

export default async function AnalysisPage() {
  const [reports, symbols] = await Promise.all([getReports(), getMarketSymbols()]);

  // Group by recommendation for the matrix view
  const byRec = reports.reduce<Record<Recommendation, number>>((acc, r) => {
    acc[r.recommendation] = (acc[r.recommendation] ?? 0) + 1;
    return acc;
  }, {} as Record<Recommendation, number>);

  const symById = new Map(symbols.map((s) => [s.symbol, s]));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">Analysis</div>
        <h1 className="text-2xl font-bold text-slate-100">AI Reasoning Layer</h1>
        <p className="text-sm text-slate-400 mt-1">
          Council-generated reports with full reasoning chains. Each report is a complete audit trail.
        </p>
      </header>

      {/* Recommendation matrix */}
      <Card title="Recommendation Matrix" subtitle="current stance by intensity">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {(Object.keys(REC_LABEL) as Recommendation[]).map((rec) => (
            <div
              key={rec}
              className={classNames(
                "p-3 rounded-md ring-1",
                REC_TONE[rec]
              )}
            >
              <div className="text-[10px] uppercase tracking-wider opacity-80">
                {REC_LABEL[rec]}
              </div>
              <div className="text-2xl font-semibold nemt-mono mt-1">
                {byRec[rec] ?? 0}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Reports feed */}
      <section className="space-y-4">
        <div className="flex items-end justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
            Reports
          </h2>
          <span className="text-[11px] text-slate-500">{reports.length} total</span>
        </div>
        {reports.map((r) => (
          <div key={r.id} className="space-y-2">
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <span className="nemt-mono">{r.symbol}</span>
              <span>·</span>
              <span>{symById.get(r.symbol)?.display ?? r.symbol}</span>
              <span>·</span>
              <span>{r.author}</span>
            </div>
            <AIReportCard report={r} />
          </div>
        ))}
      </section>
    </div>
  );
}
