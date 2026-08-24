"use client";

import type { MarketSymbol } from "@/lib/types";
import PhaseIndicator from "./PhaseIndicator";

interface MarketStateCardProps {
  symbol: MarketSymbol;
}

export default function MarketStateCard({ symbol }: MarketStateCardProps) {
  const isPositive = symbol.change24h >= 0;

  return (
    <div className="nemt-panel p-4 hover:border-amber-500/40 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-amber-400 font-mono font-bold text-lg">
            {symbol.display}
          </span>
          <PhaseIndicator phase={symbol.phase} size="sm" />
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {new Date(symbol.updatedAt).toLocaleTimeString()}
        </span>
      </div>

      {/* Price */}
      <div className="mb-4">
        <span className="text-3xl font-mono font-bold text-white tracking-tight">
          ${symbol.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
        <span
          className={`ml-2 text-sm font-mono ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}
          {symbol.change24h.toFixed(2)}%
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-3">
        {/* DCI */}
        <div className="bg-slate-900/50 rounded p-2">
          <span className="text-xs text-slate-500 block mb-1">DCI</span>
          <div className="flex items-center gap-2">
            <span className="text-lg font-mono font-bold text-amber-400">
              {symbol.dci.value.toFixed(1)}
            </span>
            <span className="text-xs text-slate-400">{symbol.dci.band}</span>
          </div>
          <div className="mt-1 h-1 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-600 to-amber-400"
              style={{ width: `${symbol.dci.value}%` }}
            />
          </div>
        </div>

        {/* Confidence */}
        <div className="bg-slate-900/50 rounded p-2">
          <span className="text-xs text-slate-500 block mb-1">CONFIDENCE</span>
          <span className="text-lg font-mono font-bold text-blue-400">
            {symbol.confidence.toFixed(1)}%
          </span>
          <div className="mt-1 h-1 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-blue-400"
              style={{ width: `${symbol.confidence}%` }}
            />
          </div>
        </div>

        {/* Volume */}
        <div className="bg-slate-900/50 rounded p-2">
          <span className="text-xs text-slate-500 block mb-1">24H VOL</span>
          <span className="text-sm font-mono font-bold text-slate-300">
            ${(symbol.volume24h / 1e9).toFixed(2)}B
          </span>
          <div className="mt-2 text-xs text-slate-500">
            H: ${symbol.high24h.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
