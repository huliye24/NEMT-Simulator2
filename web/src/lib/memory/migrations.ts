// NEMT Web Alpha 006 — Schema migrations
// ---------------------------------------------------------------
// If you change the shape of a stored value, bump
// MEMORY_SCHEMA_VERSION in keys.ts and add a step here.
// Migrations run on Memory.boot() — keep them idempotent and
// defensive (missing data is OK).
// ---------------------------------------------------------------

import { MEMORY_SCHEMA_VERSION, MemoryKeys } from "./keys";
import { LocalStore } from "./localStore";

interface VersionedBlob<T> {
  __v: number;
  data: T;
}

const VERSION_KEY = "nemt.memory.schemaVersion";

function isVersioned<T>(value: unknown): value is VersionedBlob<T> {
  return (
    typeof value === "object" &&
    value !== null &&
    "__v" in value &&
    "data" in value
  );
}

/** Run schema migrations. Safe to call repeatedly. */
export async function runMigrations(): Promise<void> {
  if (typeof window === "undefined") return;
  const stored = await LocalStore.get<number>(VERSION_KEY);
  const current = stored ?? 0;

  if (current < 1) {
    // v0 → v1: initial schema. Wrap any raw arrays we already have.
    await migrateV0ToV1();
    await LocalStore.set(VERSION_KEY, 1);
  }

  // Future migrations go here:
  // if (current < 2) { ... await LocalStore.set(VERSION_KEY, 2); }

  if (current > MEMORY_SCHEMA_VERSION) {
    console.warn(
      `[memory] Stored schema v${current} is newer than runtime v${MEMORY_SCHEMA_VERSION}. Skipping.`
    );
  }
}

async function migrateV0ToV1(): Promise<void> {
  // No-op for greenfield installs. The version wrapper exists so future
  // changes can be detected. If users already have raw arrays from earlier
  // experimentation, we leave them alone (legacy reads will still work).
  for (const key of Object.values(MemoryKeys)) {
    const raw = await LocalStore.get<unknown>(key);
    if (raw !== null && !isVersioned(raw)) {
      // Don't touch it — preserves any pre-existing data shape.
    }
  }
}
