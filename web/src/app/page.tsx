import { mockMarketData, mockAIReport, mockTradeMemory } from "@/data/mock";

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Human Judgment + AI Execution</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard title="Total P&L" value="+$930.50" change="+12.5%" positive />
        <StatCard title="Win Rate" value="68%" change="+5%" positive />
        <StatCard title="Active Trades" value="3" change="-1" neutral />
        <StatCard title="AI Confidence" value="85%" change="+2%" positive />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Overview */}
        <div className="lg:col-span-2 nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Market Overview</h2>
          <div className="space-y-3">
            {mockMarketData.map((market) => (
              <div key={market.symbol} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-white font-medium">{market.symbol}</span>
                  <span className="text-slate-400 text-sm ml-2">${market.price.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    market.phase === "markup" ? "bg-emerald-500/20 text-emerald-400" :
                    market.phase === "accumulation" ? "bg-blue-500/20 text-blue-400" :
                    market.phase === "distribution" ? "bg-amber-500/20 text-amber-400" :
                    "bg-red-500/20 text-red-400"
                  }`}>
                    {market.phase}
                  </span>
                  <span className="text-slate-400 text-sm">DCI: {market.dci}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    market.risk === "low" ? "bg-emerald-500/20 text-emerald-400" :
                    market.risk === "medium" ? "bg-amber-500/20 text-amber-400" :
                    "bg-red-500/20 text-red-400"
                  }`}>
                    {market.risk}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Report */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">AI Analysis</h2>
          <div className="space-y-4">
            <div>
              <span className="text-slate-400 text-sm">Summary</span>
              <p className="text-white mt-1">{mockAIReport.summary}</p>
            </div>
            <div>
              <span className="text-slate-400 text-sm">Recommendation</span>
              <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium ${
                mockAIReport.recommendation === "buy" ? "bg-emerald-500/20 text-emerald-400" :
                mockAIReport.recommendation === "sell" ? "bg-red-500/20 text-red-400" :
                mockAIReport.recommendation === "hold" ? "bg-amber-500/20 text-amber-400" :
                "bg-blue-500/20 text-blue-400"
              }`}>
                {mockAIReport.recommendation.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-slate-400 text-sm">Reasoning</span>
              <p className="text-slate-300 mt-1 text-sm whitespace-pre-line">{mockAIReport.reasoning}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="mt-6 nemt-card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Trades</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-slate-400 text-sm border-b border-slate-700">
                <th className="pb-3">Date</th>
                <th className="pb-3">Human Thesis</th>
                <th className="pb-3">AI Reasoning</th>
                <th className="pb-3">Result</th>
                <th className="pb-3">P&L</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {mockTradeMemory.map((trade, idx) => (
                <tr key={idx} className="border-b border-slate-800/50">
                  <td className="py-3 text-slate-300">{trade.date}</td>
                  <td className="py-3 text-slate-300">{trade.human_thesis}</td>
                  <td className="py-3 text-slate-400">{trade.ai_reasoning}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      trade.result === "win" ? "bg-emerald-500/20 text-emerald-400" :
                      trade.result === "loss" ? "bg-red-500/20 text-red-400" :
                      "bg-slate-500/20 text-slate-400"
                    }`}>
                      {trade.result}
                    </span>
                  </td>
                  <td className={`py-3 font-medium ${
                    trade.pnl && trade.pnl > 0 ? "text-emerald-400" :
                    trade.pnl && trade.pnl < 0 ? "text-red-400" :
                    "text-slate-400"
                  }`}>
                    {trade.pnl ? `${trade.pnl > 0 ? "+" : ""}$${trade.pnl.toFixed(2)}` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({
  title,
  value,
  change,
  positive,
  neutral,
}: {
  title: string;
  value: string;
  change: string;
  positive?: boolean;
  neutral?: boolean;
}) {
  return (
    <div className="nemt-card p-4">
      <span className="text-slate-400 text-sm">{title}</span>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-2xl font-bold text-white">{value}</span>
        <span className={`text-xs ${
          positive ? "text-emerald-400" : neutral ? "text-slate-400" : "text-red-400"
        }`}>
          {change}
        </span>
      </div>
    </div>
  );
}
