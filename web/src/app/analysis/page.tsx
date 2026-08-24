import { mockAIReport } from "@/data/mock";

export default function AnalysisPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Analysis</h1>
        <p className="text-slate-400">AI-powered market analysis and reasoning</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Analysis */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Current Analysis</h2>
          <div className="space-y-4">
            <div className="p-4 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400 text-sm">Summary</span>
              <p className="text-white mt-2 text-lg">{mockAIReport.summary}</p>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-slate-400">Recommendation:</span>
              <span className={`px-4 py-2 rounded-full text-sm font-bold ${
                mockAIReport.recommendation === "buy" ? "bg-emerald-500/20 text-emerald-400" :
                mockAIReport.recommendation === "sell" ? "bg-red-500/20 text-red-400" :
                mockAIReport.recommendation === "hold" ? "bg-amber-500/20 text-amber-400" :
                "bg-blue-500/20 text-blue-400"
              }`}>
                {mockAIReport.recommendation.toUpperCase()}
              </span>
            </div>

            <div className="p-4 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400 text-sm">AI Reasoning</span>
              <ul className="mt-2 space-y-2 text-slate-300">
                {mockAIReport.reasoning.split("\n").filter(Boolean).map((line, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>{line.replace(/^\d+\.\s*/, "")}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Analysis History */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Analysis History</h2>
          <div className="space-y-3">
            {[
              { date: "2025-08-24", summary: "BTC breakout confirmed", rec: "buy", confidence: 85 },
              { date: "2025-08-22", summary: "ETH accumulation phase", rec: "hold", confidence: 72 },
              { date: "2025-08-20", summary: "SOL distribution warning", rec: "sell", confidence: 68 },
            ].map((item, idx) => (
              <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">{item.date}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    item.rec === "buy" ? "bg-emerald-500/20 text-emerald-400" :
                    item.rec === "sell" ? "bg-red-500/20 text-red-400" :
                    "bg-amber-500/20 text-amber-400"
                  }`}>
                    {item.rec.toUpperCase()}
                  </span>
                </div>
                <p className="text-white">{item.summary}</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-slate-500 text-xs">Confidence:</span>
                  <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${item.confidence}%` }}
                    />
                  </div>
                  <span className="text-slate-400 text-xs">{item.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
