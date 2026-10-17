import { Card } from "@/components/Card";
import { getSystemState } from "@/lib/api";
import { classNames } from "@/lib/format";
import type { SystemModuleState } from "@/lib/types";

export default async function SystemPage() {
  const systemState = await getSystemState();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <header>
        <div className="text-[11px] uppercase tracking-wider text-amber-400 mb-1">System</div>
        <h1 className="text-2xl font-bold text-slate-100">System Status</h1>
        <p className="text-sm text-slate-400 mt-1">
          NEMT Financial OS health and module status.
        </p>
      </header>

      {/* System Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatusCard
          title="Version"
          value={systemState.version}
          status={systemState.status}
        />
        <StatusCard
          title="Uptime"
          value={calculateUptime(systemState.startedAt)}
          status="healthy"
        />
        <StatusCard
          title="Modules"
          value={`${Object.values(systemState.modules).filter((m) => m.status === "healthy").length}/${Object.keys(systemState.modules).length}`}
          status="healthy"
        />
        <StatusCard
          title="Emergency Stop"
          value={systemState.risk.emergencyStop ? "ACTIVE" : "OFF"}
          status={systemState.risk.emergencyStop ? "error" : "healthy"}
        />
      </div>

      {/* Module Status */}
      <Card title="Module Status" subtitle="All system modules">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(systemState.modules).map(([name, module]) => (
            <ModuleCard
              key={name}
              name={name}
              module={module}
            />
          ))}
        </div>
      </Card>

      {/* Risk Status */}
      <Card title="Risk Management" subtitle="Current risk parameters">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <RiskMetric
            label="Daily Loss"
            value={`$${systemState.risk.dailyLoss.toFixed(2)}`}
            limit={`$${systemState.risk.dailyLossLimit}`}
            status={Math.abs(systemState.risk.dailyLoss) > systemState.risk.dailyLossLimit * 0.8 ? "warning" : "ok"}
          />
          <RiskMetric
            label="Max Position"
            value={`$${systemState.risk.maxPositionSize.toLocaleString()}`}
            limit=""
            status="ok"
          />
          <RiskMetric
            label="Position Ratio"
            value={`${(systemState.risk.maxPositionRatio * 100).toFixed(0)}%`}
            limit=""
            status="ok"
          />
          <RiskMetric
            label="Emergency"
            value={systemState.risk.emergencyStop ? "STOP" : "OFF"}
            limit=""
            status={systemState.risk.emergencyStop ? "error" : "ok"}
          />
        </div>
      </Card>

      {/* AI Council */}
      <Card title="AI Council" subtitle="Multi-agent system status">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Last Verdict</span>
            <span className="text-slate-100">{systemState.aiCouncil.lastVerdict.recommendation}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Confidence</span>
            <span className="text-blue-400">{systemState.aiCouncil.lastVerdict.confidence}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Outcome</span>
            <span className={classNames(
              "px-2 py-0.5 rounded text-xs",
              systemState.aiCouncil.lastVerdict.outcome === "CONSENSUS" ? "bg-emerald-500/10 text-emerald-400" :
              systemState.aiCouncil.lastVerdict.outcome === "SPLIT" ? "bg-amber-500/10 text-amber-400" :
              "bg-blue-500/10 text-blue-400"
            )}>
              {systemState.aiCouncil.lastVerdict.outcome}
            </span>
          </div>
          <div className="pt-4 border-t border-slate-800">
            <span className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">Active Agents</span>
            <div className="flex flex-wrap gap-2">
              {systemState.aiCouncil.agents.map((agent) => (
                <span
                  key={agent.id}
                  className="text-xs px-2 py-1 rounded bg-nemt-bg-elevated text-slate-300 border border-nemt-border"
                >
                  {agent.id} ({(agent.weight * 100).toFixed(0)}%)
                </span>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Footer */}
      <footer className="border-t border-slate-800 pt-6">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>NEMT Financial OS v{systemState.version}</span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            All systems operational
          </span>
        </div>
      </footer>
    </div>
  );
}

function StatusCard({ title, value, status }: { title: string; value: string; status: string }) {
  const statusColors: Record<string, string> = {
    healthy: "bg-emerald-500",
    running: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-red-500",
  };

  return (
    <div className="nemt-panel p-4">
      <div className="flex items-center gap-2">
        <span className={classNames("w-2 h-2 rounded-full", statusColors[status] || "bg-slate-500")} />
        <span className="text-xs text-slate-500 uppercase tracking-wider">{title}</span>
      </div>
      <div className="text-lg font-semibold text-slate-100 mt-2">{value}</div>
    </div>
  );
}

function ModuleCard({
  name,
  module,
}: {
  name: string;
  module: SystemModuleState;
}) {
  const statusColors: Record<string, string> = {
    healthy: "text-emerald-400",
    warning: "text-amber-400",
    error: "text-red-400",
  };

  return (
    <div className="bg-nemt-bg-deep rounded-lg p-4 border border-nemt-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-100 capitalize">{name}</span>
        <span className={classNames("text-xs", statusColors[module.status] || "text-slate-400")}>
          {module.status}
        </span>
      </div>
      {module.version && (
        <div className="text-xs text-slate-500">v{module.version}</div>
      )}
      {module.symbols && (
        <div className="text-xs text-slate-500">{module.symbols} symbols</div>
      )}
      {module.agents && (
        <div className="text-xs text-slate-500">{module.agents} agents</div>
      )}
      {module.mode && (
        <div className="text-xs text-slate-500 capitalize">{module.mode} mode</div>
      )}
      <div className="text-xs text-slate-600 mt-2">
        Last update:{" "}
        {module.lastUpdate ? new Date(module.lastUpdate).toLocaleTimeString() : "—"}
      </div>
    </div>
  );
}

function RiskMetric({ label, value, limit, status }: { label: string; value: string; limit: string; status: string }) {
  const statusColors: Record<string, string> = {
    ok: "text-emerald-400",
    warning: "text-amber-400",
    error: "text-red-400",
  };

  return (
    <div className="bg-nemt-bg-deep rounded-lg p-3 border border-nemt-border">
      <span className="text-xs text-slate-500 block mb-1">{label}</span>
      <span className={classNames("text-lg font-semibold", statusColors[status] || "text-slate-100")}>
        {value}
      </span>
      {limit && <span className="text-xs text-slate-500 ml-2">/ {limit}</span>}
    </div>
  );
}

function calculateUptime(startedAt: string): string {
  const start = new Date(startedAt).getTime();
  const now = Date.now();
  const diff = now - start;

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  }
  return `${hours}h`;
}
