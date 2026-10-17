"use client";

import { useEffect, useState } from "react";
import { Card } from "./Card";
import { Memory } from "@/lib/memory";

interface StorageReport {
  available: boolean;
  localBytes: number;
  idbAvailable: boolean;
  keyCount: number;
}

function detectStorage(): StorageReport {
  if (typeof window === "undefined") {
    return { available: false, localBytes: 0, idbAvailable: false, keyCount: 0 };
  }
  let localBytes = 0;
  let keyCount = 0;
  try {
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const k = window.localStorage.key(i);
      if (!k || !k.startsWith("nemt:")) continue;
      const v = window.localStorage.getItem(k) ?? "";
      localBytes += k.length + v.length;
      keyCount += 1;
    }
  } catch {
    /* storage unavailable */
  }
  return {
    available: true,
    localBytes,
    idbAvailable: "indexedDB" in window,
    keyCount,
  };
}

/**
 * Settings page panel that exposes what's stored locally.
 * Lives in a client component because storage detection
 * requires `window`.
 */
export function MemoryPanel() {
  const [report, setReport] = useState<StorageReport | null>(null);
  const [counts, setCounts] = useState({
    analyses: 0,
    journal: 0,
    pinned: 0,
    verdicts: 0,
  });
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    // Read browser storage after hydration to avoid a server/client mismatch.
    let cancelled = false;
    const timer = window.setTimeout(() => {
      if (cancelled) return;
      setReport(detectStorage());
      void Memory.Stats.summary().then((next) => {
        if (!cancelled) setCounts(next);
      });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  const refresh = async () => {
    setReport(detectStorage());
    setCounts(await Memory.Stats.summary());
  };

  const onForget = async () => {
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 4000);
      return;
    }
    await Memory.Forget.all();
    setConfirming(false);
    await refresh();
    window.location.reload();
  };

  return (
    <Card title="Financial Memory" subtitle="local persistence layer (Alpha 006+)" accent>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
        <Row
          label="Storage backend"
          value={
            report?.idbAvailable
              ? "IndexedDB + localStorage"
              : report?.available
              ? "localStorage (fallback)"
              : "Unavailable"
          }
        />
        <Row
          label="localStorage usage"
          value={
            report
              ? `${(report.localBytes / 1024).toFixed(1)} KB · ${report.keyCount} keys`
              : "…"
          }
        />
        <Row label="Stored analyses" value={counts.analyses.toString()} />
        <Row label="Council verdicts" value={counts.verdicts.toString()} />
        <Row label="Stored journal entries" value={counts.journal.toString()} />
        <Row label="Pinned analyses" value={counts.pinned.toString()} />
        <Row label="Schema version" value="v1" />
      </dl>

      <div className="mt-5 pt-4 border-t border-nemt-border flex flex-wrap items-center gap-3">
        <button
          onClick={refresh}
          className="text-[11px] uppercase tracking-wider text-slate-300 hover:text-slate-100 transition-colors"
        >
          ↻ Refresh
        </button>
        <button
          onClick={onForget}
          className={
            confirming
              ? "text-[11px] uppercase tracking-wider text-rose-200 nemt-mono"
              : "text-[11px] uppercase tracking-wider text-rose-300/80 hover:text-rose-300 transition-colors"
          }
        >
          {confirming ? "Click again to confirm" : "Forget Everything"}
        </button>
        <span className="text-[10px] text-slate-500 ml-auto">
          Stored only in this browser · never leaves your device
        </span>
      </div>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b nemt-divider pb-2 last:border-0 last:pb-0">
      <dt className="text-slate-400 text-[12px] uppercase tracking-wider">
        {label}
      </dt>
      <dd className="text-slate-100 nemt-mono text-[13px] font-medium text-right">
        {value}
      </dd>
    </div>
  );
}
