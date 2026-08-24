import { Card } from "./Card";
import type { AIReport, Recommendation } from "@/lib/types";
import { classNames, formatPercent, formatRelativeTime } from "@/lib/format";

const REC_STYLES: Record<Recommendation, string> = {
  STRONG_BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/30",
  BUY: "text-emerald-300 bg-emerald-500/10 ring-emerald-500/20",
  HOLD: "text-slate-300 bg-slate-500/10 ring-slate-500/30",
  REDUCE: "text-amber-300 bg-amber-500/10 ring-amber-500/30",
  SELL: "text-rose-300 bg-rose-500/10 ring-rose-500/30",
  WAIT: "text-slate-300 bg-slate-500/10 ring-slate-500/20",
};

interface AIReportCardProps {
  report: AIReport;
}

export function AIReportCard({ report }: AIReportCardProps) {
  return (
    <Card
      accent
      title={
        <div className="flex items-center gap-2">
          <span className="text-amber-300">●</span>
          <span className="truncate">{report.title}</span>
        </div>
      }
      subtitle={
        <span>
          {report.symbol} · {report.author} · {formatRelativeTime(report.generatedAt)}
        </span>
      }
      rightSlot={
        <span className={classNames("nemt-phase-chip ring-1", REC_STYLES[report.recommendation])}>
          {report.recommendation.replace("_", " ")}
        </span>
      }
    >
      <p className="text-sm text-slate-200 leading-relaxed mb-4">{report.summary}</p>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Metric label="Confidence" value={`${report.confidence.toFixed(1)}%`} />
        <Metric label="DCI" value={report.dci.toFixed(1)} />
        <Metric label="Phase" value={report.phase} />
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mb-2">
          Reasoning
        </div>
        <ul className="space-y-1.5">
          {report.reasoning.map((r, i) => (
            <li
              key={i}
              className="text-[13px] text-slate-300 leading-relaxed pl-3 relative before:content-['–'] before:absolute before:left-0 before:text-amber-500/60"
            >
              {r}
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-3 py-2 rounded-md bg-nemt-bg-elevated/60 ring-1 ring-amber-500/10">
      <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">{label}</div>
      <div className="text-sm font-semibold nemt-mono text-slate-100 mt-0.5">{value}</div>
    </div>
  );
}

export { formatPercent };
