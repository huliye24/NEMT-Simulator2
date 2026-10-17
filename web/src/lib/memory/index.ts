// NEMT Web Alpha 006 — Financial Memory System (public API)
// ---------------------------------------------------------------
// The single import page/component code should reach for. Wraps
// the underlying KeyValueStores with typed, named accessors and
// runs schema migrations on boot.
// ---------------------------------------------------------------

import type { Analysis, CouncilVerdict, JournalEntry } from "@/lib/types";
import { LocalStore } from "./localStore";
import { IdbStore } from "./idbStore";
import { MemoryKeys, type MemoryKey } from "./keys";
import { runMigrations } from "./migrations";

// ---------- types ----------

export interface Preferences {
  /** Default starting capital shown on the simulation page (USDT). */
  startingCapital: number;
  /** Last phase filter applied to the Market page. */
  defaultPhaseFilter?: string;
  /** Mark an analysis row as "featured" on the dashboard. */
  featuredAnalysisId?: string;
}

export interface ThesisDraft {
  macroView: string;
  marketJudgment: string;
  riskFactors: string;
  actionPlan: string;
  /** ISO timestamp of last edit; used to discard stale drafts. */
  updatedAt: string;
}

// ---------- implementation ----------

const local = LocalStore;
const idb = new IdbStore();

let booted = false;
let bootPromise: Promise<void> | null = null;

/** Call once from a client component to ensure migrations have run. */
export function boot(): Promise<void> {
  if (booted) return Promise.resolve();
  if (!bootPromise) {
    bootPromise = runMigrations().then(() => {
      booted = true;
    });
  }
  return bootPromise;
}

// ---------- typed accessors ----------
// Each accessor pairs a MemoryKey with its expected shape and the
// backing store. Small synchronous-feeling prefs go to localStorage,
// lists and large blobs go to IndexedDB.

export const Memory = {
  // ---- Analyses (large, list-shaped) ----
  Analyses: {
    async list(): Promise<Analysis[]> {
      await boot();
      const raw = await idb.get<Analysis[]>(MemoryKeys.Analyses);
      return raw ?? [];
    },
    async add(analysis: Analysis): Promise<void> {
      await boot();
      const all = await this.list();
      const next = [analysis, ...all.filter((a) => a.id !== analysis.id)];
      await idb.set(MemoryKeys.Analyses, next);
    },
    async update(id: string, patch: Partial<Analysis>): Promise<Analysis | null> {
      await boot();
      const all = await this.list();
      const idx = all.findIndex((a) => a.id === id);
      if (idx === -1) return null;
      const merged: Analysis = { ...all[idx], ...patch };
      all[idx] = merged;
      await idb.set(MemoryKeys.Analyses, all);
      return merged;
    },
    async remove(id: string): Promise<void> {
      await boot();
      const all = await this.list();
      await idb.set(
        MemoryKeys.Analyses,
        all.filter((a) => a.id !== id)
      );
    },
    async clear(): Promise<void> {
      await boot();
      await idb.remove(MemoryKeys.Analyses);
    },
  },

  // ---- Journal (user-authored entries) ----
  Journal: {
    async list(): Promise<JournalEntry[]> {
      await boot();
      const raw = await idb.get<JournalEntry[]>(MemoryKeys.JournalEntries);
      return raw ?? [];
    },
    async add(entry: JournalEntry): Promise<void> {
      await boot();
      const all = await this.list();
      const next = [entry, ...all.filter((e) => e.id !== entry.id)];
      await idb.set(MemoryKeys.JournalEntries, next);
    },
    async remove(id: string): Promise<void> {
      await boot();
      const all = await this.list();
      await idb.set(
        MemoryKeys.JournalEntries,
        all.filter((e) => e.id !== id)
      );
    },
    async clear(): Promise<void> {
      await boot();
      await idb.remove(MemoryKeys.JournalEntries);
    },
  },

  // ---- Thesis draft (small, sync-shaped, frequent writes) ----
  ThesisDraft: {
    async get(): Promise<ThesisDraft | null> {
      await boot();
      return local.get<ThesisDraft>(MemoryKeys.ThesisDraft);
    },
    async set(draft: ThesisDraft): Promise<void> {
      await boot();
      await local.set(MemoryKeys.ThesisDraft, draft);
    },
    async clear(): Promise<void> {
      await boot();
      await local.remove(MemoryKeys.ThesisDraft);
    },
  },

  // ---- Preferences (small, sync-shaped, infrequent writes) ----
  Preferences: {
    async get(): Promise<Preferences> {
      await boot();
      const raw = await local.get<Preferences>(MemoryKeys.Preferences);
      return raw ?? { startingCapital: 100_000 };
    },
    async set(prefs: Partial<Preferences>): Promise<Preferences> {
      await boot();
      const merged: Preferences = { ...(await this.get()), ...prefs };
      await local.set(MemoryKeys.Preferences, merged);
      return merged;
    },
    async clear(): Promise<void> {
      await boot();
      await local.remove(MemoryKeys.Preferences);
    },
  },

  // ---- Council verdicts (Alpha 009, list-shaped) ----
  Council: {
    async list(): Promise<CouncilVerdict[]> {
      await boot();
      const raw = await idb.get<CouncilVerdict[]>(MemoryKeys.CouncilVerdicts);
      return raw ?? [];
    },
    async add(verdict: CouncilVerdict): Promise<void> {
      await boot();
      const all = await this.list();
      const next = [verdict, ...all.filter((v) => v.id !== verdict.id)];
      await idb.set(MemoryKeys.CouncilVerdicts, next);
    },
    async remove(id: string): Promise<void> {
      await boot();
      const all = await this.list();
      await idb.set(
        MemoryKeys.CouncilVerdicts,
        all.filter((v) => v.id !== id)
      );
    },
    async clear(): Promise<void> {
      await boot();
      await idb.remove(MemoryKeys.CouncilVerdicts);
    },
  },

  // ---- Pinned analyses (small set of IDs) ----
  PinnedAnalyses: {
    async list(): Promise<string[]> {
      await boot();
      return (await local.get<string[]>(MemoryKeys.PinnedAnalyses)) ?? [];
    },
    async toggle(id: string): Promise<string[]> {
      await boot();
      const current = await this.list();
      const next = current.includes(id)
        ? current.filter((x) => x !== id)
        : [id, ...current];
      await local.set(MemoryKeys.PinnedAnalyses, next);
      return next;
    },
    async clear(): Promise<void> {
      await boot();
      await local.remove(MemoryKeys.PinnedAnalyses);
    },
  },

  // ---- Operator-facing helpers ----
  Stats: {
    /** Cheap summary for the Header indicator. */
    async summary(): Promise<{
      analyses: number;
      journal: number;
      pinned: number;
      verdicts: number;
    }> {
      await boot();
      const [analyses, journal, pinned, verdicts] = await Promise.all([
        Memory.Analyses.list(),
        Memory.Journal.list(),
        Memory.PinnedAnalyses.list(),
        Memory.Council.list(),
      ]);
      return {
        analyses: analyses.length,
        journal: journal.length,
        pinned: pinned.length,
        verdicts: verdicts.length,
      };
    },
  },

  Forget: {
    /** Wipe all memory. Settings → "Forget Everything". */
    async all(): Promise<void> {
      await boot();
      await Promise.all([local.clear(), idb.clear()]);
      // Re-mark schema version after wipe so future migrations stay sane.
      booted = false;
      bootPromise = null;
      await boot();
    },
  },

  /** Low-level escape hatch — typed, but you should usually use the helpers above. */
  raw: {
    get<T>(store: "local" | "idb", key: MemoryKey): Promise<T | null> {
      return store === "local" ? local.get<T>(key) : idb.get<T>(key);
    },
    set<T>(store: "local" | "idb", key: MemoryKey, value: T): Promise<void> {
      return store === "local"
        ? local.set<T>(key, value)
        : idb.set<T>(key, value);
    },
  },
};

// ---------- React-friendly helpers ----------
// Avoid requiring a full Zustand dependency just for one indicator.

import { useEffect, useState } from "react";

export interface MemoryCounts {
  analyses: number;
  journal: number;
  pinned: number;
  verdicts: number;
  ready: boolean;
}

/** Subscribe to memory counts; refreshes when analyses/journal change. */
export function useMemoryCounts(): MemoryCounts {
  const [counts, setCounts] = useState<MemoryCounts>({
    analyses: 0,
    journal: 0,
    pinned: 0,
    verdicts: 0,
    ready: false,
  });

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      const s = await Memory.Stats.summary();
      if (!cancelled) setCounts({ ...s, ready: true });
    };
    refresh();
    const onChange = () => refresh();
    window.addEventListener("nemt:memory-changed", onChange);
    return () => {
      cancelled = true;
      window.removeEventListener("nemt:memory-changed", onChange);
    };
  }, []);

  return counts;
}

/** Emit from any memory mutation; useMemoryCounts subscribers will refresh. */
export function notifyMemoryChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("nemt:memory-changed"));
  }
}
