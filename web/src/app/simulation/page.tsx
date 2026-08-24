"use client";

import { useState } from "react";
import { mockMarketData } from "@/data/mock";

export default function SimulationPage() {
  const [selectedSymbol, setSelectedSymbol] = useState(mockMarketData[0].symbol);
  const [position, setPosition] = useState<"long" | "short" | null>(null);
  const [amount, setAmount] = useState("");

  const selectedMarket = mockMarketData.find(m => m.symbol === selectedSymbol);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Simulation</h1>
        <p className="text-slate-400">Paper trading with AI guidance</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Panel */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">New Trade</h2>

          <div className="space-y-4">
            {/* Symbol Select */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">Symbol</label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                {mockMarketData.map((m) => (
                  <option key={m.symbol} value={m.symbol}>
                    {m.symbol} - ${m.price.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>

            {/* Position Type */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">Position</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setPosition("long")}
                  className={`px-4 py-3 rounded-lg font-medium transition-all ${
                    position === "long"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50"
                      : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
                  }`}
                >
                  LONG
                </button>
                <button
                  onClick={() => setPosition("short")}
                  className={`px-4 py-3 rounded-lg font-medium transition-all ${
                    position === "short"
                      ? "bg-red-500/20 text-red-400 border border-red-500/50"
                      : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
                  }`}
                >
                  SHORT
                </button>
              </div>
            </div>

            {/* Amount */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">Amount (USDT)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="Enter amount"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Market Info */}
            {selectedMarket && (
              <div className="p-4 bg-slate-800/50 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Current Price</span>
                  <span className="text-white">${selectedMarket.price.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-slate-400">Phase</span>
                  <span className="text-blue-400">{selectedMarket.phase}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-slate-400">DCI</span>
                  <span className="text-purple-400">{selectedMarket.dci}</span>
                </div>
              </div>
            )}

            {/* Execute Button */}
            <button
              disabled={!position || !amount}
              className="w-full py-3 rounded-lg font-medium bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-all"
            >
              Execute Simulation Trade
            </button>
          </div>
        </div>

        {/* Active Simulations */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Active Simulations</h2>
          <div className="space-y-3">
            {[
              { symbol: "BTC/USDT", type: "long", entry: 65432, current: 67432, pnl: 3.05 },
              { symbol: "ETH/USDT", type: "short", entry: 3520, current: 3456, pnl: 1.82 },
            ].map((trade, idx) => (
              <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">{trade.symbol}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    trade.type === "long" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                  }`}>
                    {trade.type.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Entry: ${trade.entry.toLocaleString()}</span>
                  <span className="text-slate-400">Current: ${trade.current.toLocaleString()}</span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-slate-400 text-sm">P&L</span>
                  <span className={`font-medium ${trade.pnl > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {trade.pnl > 0 ? "+" : ""}{trade.pnl}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
