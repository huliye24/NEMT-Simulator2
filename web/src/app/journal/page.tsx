import { mockTradeMemory } from "@/data/mock";

export default function JournalPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Journal</h1>
        <p className="text-slate-400">Trade memory and learning</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="nemt-card p-4">
          <span className="text-slate-400 text-sm">Total Trades</span>
          <span className="text-2xl font-bold text-white mt-1 block">24</span>
        </div>
        <div className="nemt-card p-4">
          <span className="text-slate-400 text-sm">Win Rate</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">68%</span>
        </div>
        <div className="nemt-card p-4">
          <span className="text-slate-400 text-sm">Total P&L</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">+$2,450</span>
        </div>
        <div className="nemt-card p-4">
          <span className="text-slate-400 text-sm">Avg Trade</span>
          <span className="text-2xl font-bold text-white mt-1 block">$102</span>
        </div>
      </div>

      {/* Trade Log */}
      <div className="nemt-card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Trade Memory</h2>
        <div className="space-y-4">
          {mockTradeMemory.map((trade, idx) => (
            <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400 text-sm">{trade.date}</span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  trade.result === "win" ? "bg-emerald-500/20 text-emerald-400" :
                  trade.result === "loss" ? "bg-red-500/20 text-red-400" :
                  "bg-slate-500/20 text-slate-400"
                }`}>
                  {trade.result.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-500 text-xs uppercase tracking-wide">Human Thesis</span>
                  <p className="text-white mt-1">{trade.human_thesis}</p>
                </div>
                <div>
                  <span className="text-slate-500 text-xs uppercase tracking-wide">AI Reasoning</span>
                  <p className="text-slate-300 mt-1">{trade.ai_reasoning}</p>
                </div>
              </div>

              {trade.pnl !== undefined && (
                <div className="mt-3 pt-3 border-t border-slate-700/50 flex items-center justify-between">
                  <span className="text-slate-400 text-sm">P&L</span>
                  <span className={`text-lg font-bold ${
                    trade.pnl > 0 ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {trade.pnl > 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
