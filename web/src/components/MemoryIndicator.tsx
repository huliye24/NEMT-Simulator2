"use client";

import { useMemoryCounts } from "@/lib/memory";
import { classNames } from "@/lib/format";

/**
 * Tiny status badge for the Header showing how many records the
 * Financial Memory layer currently holds. Updates live as the
 * user adds analyses / journal entries / pins.
 */
export function MemoryIndicator() {
  const { analyses, journal, pinned, ready } = useMemoryCounts();
  const total = analyses + journal + pinned;

  return (
    <div
      className={classNames(
        "flex items-center gap-1.5 px-2 py-1 rounded-md ring-1 transition-all",
        ready
          ? total > 0
            ? "bg-amber-500/10 ring-amber-500/30"
            : "bg-slate-800/40 ring-slate-700/40"
          : "bg-slate-800/40 ring-slate-700/40"
      )}
      title="Local Financial Memory"
    >
      <span
        className={classNames(
          "w-1.5 h-1.5 rounded-full",
          ready
            ? total > 0
              ? "bg-amber-400 animate-pulse"
              : "bg-slate-500"
            : "bg-slate-600"
        )}
      />
      <span
        className={classNames(
          "text-[10px] font-semibold tracking-wider uppercase",
          ready
            ? total > 0
              ? "text-amber-300 nemt-mono"
              : "text-slate-500 nemt-mono"
            : "text-slate-600 nemt-mono"
        )}
      >
        Mem
        {ready ? ` · ${total}` : " · …"}
      </span>
    </div>
  );
}
