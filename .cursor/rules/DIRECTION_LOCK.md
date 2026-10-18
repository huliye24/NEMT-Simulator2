# NEMT Direction Lock

**Status:** Authoritative
**Confirmed by:** Maintainer (`huliye24`)
**Confirmed on:** 2026-10-18, via issue #20
**Scope:** All human and AI contributors.

This file is the authoritative direction lock for repository work. Read it before
making any change. If a summary or duplicate list elsewhere (including
`AGENTS.md`) conflicts with this file, this file governs; report the conflict
instead of following the broader text.

## Allowed scope

Changes are permitted only under these repository paths:

- `/web/src/components`
- `/web/src/stores`
- `/web/src/pages`
- `/nemt_os/services`
- `/docs`

## Forbidden scope

These paths must not be modified under this lock:

- `/core`
- `/database`
- `/auth`
- `/.git`

Any path not explicitly listed in the allowed scope is **out of scope** and
requires prior, separate maintainer approval.

## Operating rules

1. Read this lock before any modification.
2. If this file is missing, unreadable, or conflicts with another guardrail, stop
   and report the gap. Do not infer or assume permission.
3. Do not silently substitute rules, broaden the allowed scope, or weaken any
   existing protection.
4. Work outside the allowed scope requires a separate, explicit maintainer
   approval and its own narrowly scoped task and PR.
5. This lock does not authorize credential handling, deployment changes, Git
   history rewrites, force-pushes, or batch deletions. Those require separate
   explicit approval and remain subject to `docs/ENGINEERING_PROTOCOL.md`,
   `docs/MICRO_TASK_PROTOCOL.md`, PAPER/LIVE isolation and least-privilege rules.
6. Changes to this file require their own maintainer-approved, narrowly scoped
   governance PR.
