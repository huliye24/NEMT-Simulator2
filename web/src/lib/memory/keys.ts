// NEMT Web Alpha 006 — Financial Memory System
// ---------------------------------------------------------------
// Type-safe keys for every persistent value. Keep these stable:
// they map 1:1 to storage buckets. Renaming a key means writing
// a migration.
// ---------------------------------------------------------------

export const MemoryKeys = {
  /** Local-only analysis history (HumanThesis → AI reasoning → decision) */
  Analyses: "nemt.memory.analyses",
  /** Locally-authored journal entries (merged on top of mock journal) */
  JournalEntries: "nemt.memory.journal",
  /** Free-form draft of the HumanThesis form, restored on reload */
  ThesisDraft: "nemt.memory.thesisDraft",
  /** User preferences (default phase filter, starting capital, theme) */
  Preferences: "nemt.memory.preferences",
  /** Bookmarks/pinned analyses for the operator */
  PinnedAnalyses: "nemt.memory.pinnedAnalyses",
  /** Multi-Agent Council session transcripts (Alpha 009) */
  CouncilVerdicts: "nemt.memory.councilVerdicts",
} as const;

export type MemoryKey = (typeof MemoryKeys)[keyof typeof MemoryKeys];

/** Current memory schema version. Bump when shape changes; add a migration. */
export const MEMORY_SCHEMA_VERSION = 1;
