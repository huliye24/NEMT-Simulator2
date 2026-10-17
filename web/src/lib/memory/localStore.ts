// NEMT Web Alpha 006 — localStorage implementation
// ---------------------------------------------------------------
// Good for small JSON blobs: preferences, drafts, pinned IDs.
// Large objects (analysis history, journal entries) should use
// the IndexedDB implementation instead.
// ---------------------------------------------------------------

import type { KeyValueStore } from "./storage";

const STORAGE_NAMESPACE = "nemt:";

function namespaced(key: string): string {
  return `${STORAGE_NAMESPACE}${key}`;
}

export const LocalStore: KeyValueStore = {
  async get<T>(key: string): Promise<T | null> {
    if (typeof window === "undefined") return null;
    try {
      const raw = window.localStorage.getItem(namespaced(key));
      if (raw === null) return null;
      return JSON.parse(raw) as T;
    } catch (err) {
      // Quota exceeded, JSON parse failure, or storage disabled.
      // We never want memory access to crash the UI.
      console.warn(`[memory] LocalStore.get(${key}) failed:`, err);
      return null;
    }
  },

  async set<T>(key: string, value: T): Promise<void> {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(namespaced(key), JSON.stringify(value));
    } catch (err) {
      console.warn(`[memory] LocalStore.set(${key}) failed:`, err);
    }
  },

  async remove(key: string): Promise<void> {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.removeItem(namespaced(key));
    } catch (err) {
      console.warn(`[memory] LocalStore.remove(${key}) failed:`, err);
    }
  },

  async keys(prefix?: string): Promise<string[]> {
    if (typeof window === "undefined") return [];
    const all: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const raw = window.localStorage.key(i);
      if (!raw || !raw.startsWith(STORAGE_NAMESPACE)) continue;
      const unprefixed = raw.slice(STORAGE_NAMESPACE.length);
      if (!prefix || unprefixed.startsWith(prefix)) {
        all.push(unprefixed);
      }
    }
    return all;
  },

  async clear(): Promise<void> {
    if (typeof window === "undefined") return;
    const doomed: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const raw = window.localStorage.key(i);
      if (raw && raw.startsWith(STORAGE_NAMESPACE)) doomed.push(raw);
    }
    for (const k of doomed) window.localStorage.removeItem(k);
  },
};
