import { mockMarketData } from "@/data/mock";

export default function MarketPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Market</h1>
        <p className="text-slate-400">Real-time market phase and DCI analysis</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockMarketData.map((market) => (
          <div key={market.symbol} className="nemt-card p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xl font-bold text-white">{market.symbol}</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                market.phase === "markup" ? "bg-emerald-500/20 text-emerald-400" :
                market.phase === "accumulation" ? "bg-blue-500/20 text-blue-400" :
                market.phase === "distribution" ? "bg-amber-500/20 text-amber-400" :
                "bg-red-500/20 text-red-400"
              }`}>
                {market.phase}
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-400">Price</span>
                <span className="text-white font-mono">${market.price.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">DCI</span>
                <span className="text-white font-mono">{market.dci}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Confidence</span>
                <span className="text-white font-mono">{(market.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk</span>
                <span className={`font-medium ${
                  market.risk === "low" ? "text-emerald-400" :
                  market.risk === "medium" ? "text-amber-400" :
                  "text-red-400"
                }`}>
                  {market.risk.toUpperCase()}
                </span>
              </div>
            </div>

            {/* DCI Bar */}
            <div className="mt-4">
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${market.dci}%` }}
                />
              </div>
              <span className="text-xs text-slate-500 mt-1">Dynamic Cycle Index</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
