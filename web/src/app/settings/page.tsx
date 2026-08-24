import { Card } from "@/components/Card";


export default function SettingsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">Settings</div>
        <h1 className="text-2xl font-bold text-slate-100">System Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Foundation-only configuration. Live settings will land in later NEMT modules.
        </p>
      </header>

      <Card title="Environment" subtitle="read-only build info">
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <Row label="Build" value="NEMT Web Alpha · 002" />
          <Row label="Stage" value="Foundation" />
          <Row label="Data Source" value="Local Mock JSON" />
          <Row label="Live Trading" value="Disabled" tone="warn" />
          <Row label="Framework" value="Next.js 16 App Router" />
          <Row label="Theme" value="Bloomberg · Amber Gold" />
        </dl>
      </Card>

      <Card title="Data Sources" subtitle="what feeds the dashboard today">
        <ul className="space-y-2 text-sm">
          <SourceRow file="src/data/market-state.json" desc="aggregate market phase, DCI, confidence" />
          <SourceRow file="src/data/market.json" desc="per-symbol price, phase, DCI" />
          <SourceRow file="src/data/report.json" desc="AI reasoning reports" />
          <SourceRow file="src/data/portfolio.json" desc="current positions and P/L" />
          <SourceRow file="src/data/trades.json" desc="open and closed paper trades" />
          <SourceRow file="src/data/journal.json" desc="trading journal entries" />
        </ul>
      </Card>

      <Card title="Roadmap" subtitle="what unlocks next">
        <ul className="space-y-2 text-sm text-slate-300">
          {[
            "003 · Dashboard Intelligence — live data adapters, websocket feeds",
            "004 · AI Reasoning Layer — full multi-agent council",
            "005 · Paper Trading — execution simulator with P/L replay",
            "006 · Financial Memory — long-term signal retention",
            "007 · NEMT Engine API — FastAPI backend integration",
            "008 · Binance Execution Layer — read-only market data",
            "009 · Multi-Agent Council — coordinated reasoning",
            "010 · Financial OS — unified operator surface",
          ].map((item) => (
            <li
              key={item}
              className="pl-3 relative before:content-['›'] before:absolute before:left-0 before:text-amber-500/70"
            >
              {item}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function Row({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "warn";
}) {
  return (
    <div className="flex items-center justify-between border-b nemt-divider pb-2 last:border-0 last:pb-0">
      <dt className="text-slate-400 text-[12px] uppercase tracking-wider">{label}</dt>
      <dd
        className={
          tone === "warn"
            ? "text-amber-300 nemt-mono text-[13px] font-medium"
            : "text-slate-100 nemt-mono text-[13px] font-medium"
        }
      >
        {value}
      </dd>
    </div>
  );
}

function SourceRow({ file, desc }: { file: string; desc: string }) {
  return (
    <li className="flex items-center justify-between gap-4 px-3 py-2 rounded-md bg-nemt-bg-elevated/60 ring-1 ring-amber-500/10">
      <code className="text-[12px] nemt-mono text-amber-300">{file}</code>
      <span className="text-[12px] text-slate-400 text-right">{desc}</span>
    </li>
  );
}
