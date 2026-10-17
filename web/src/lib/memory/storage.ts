// NEMT Web Alpha 006 — KeyValueStore abstraction
// ---------------------------------------------------------------
// The Memory layer talks to a KeyValueStore. Two implementations:
//   - LocalStore  → window.localStorage (sync, small values, ~5MB cap)
//   - IdbStore    → window.indexedDB  (async, large values, ~hundreds of MB)
//
// Both share this interface so call sites stay identical.
// ---------------------------------------------------------------

export interface KeyValueStore {
  /** Returns the value or null if missing. */
  get<T>(key: string): Promise<T | null>;
  /** Writes the value. Overwrites silently. */
  set<T>(key: string, value: T): Promise<void>;
  /** Removes the key. Missing keys are not an error. */
  remove(key: string): Promise<void>;
  /** Lists all keys with the given prefix (used for migrations / debugging). */
  keys(prefix?: string): Promise<string[]>;
  /** Bulk clear — only used by Settings → "Forget Everything". */
  clear(): Promise<void>;
}
