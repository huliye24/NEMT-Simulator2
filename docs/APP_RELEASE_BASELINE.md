# NEMT App Release Baseline

## Frozen baseline

- Product: Emergentix / NEMT Trade
- Baseline: Hong Kong production UI running on 2026-10-22 at 15:27 CST
- Release identity: `v0.1.0-hk.20261022.1527`
- Source archive: `docs/rollback-backups/nemt-cloud-hk-20261022-1527-v0.1.0.zip`
- SHA-256: `B32E47E99A5667666A11DBACAB83E048AFCE184C3F41650BBE23EC292E3E85BE`
- Production source: `/opt/nemt-app/web`
- Production services inspected read-only: `nemt-web.service`, `nemt-api.service`

The archive contains the deployed `web/src`, `web/public`, package manifests, and Next configuration. It excludes credentials, databases, environment files, build caches, and `node_modules`.

## Product direction

The Hong Kong version is the visual and interaction baseline. It preserves the complete workspace instead of reducing the application to a few functional screens:

- Portfolio
- Markets
- Strategies
- Paper Trading
- Research
- Experiments
- Personal Space
- Settings

The local and Hong Kong frontends were compared by SHA-256. Of 155 deployed frontend files, 118 matched the local workspace, 21 differed, and 16 deployed files were missing locally. The missing files include the experiment workspace, diary canvas, music playback provider, position detail, research notes, and the client backtest engine.

## Release contract

Every installable build must have all of the following before it can be put on a phone:

1. A SemVer release name, for example `0.1.0`.
2. An Android integer version code that only increases.
3. A source snapshot or Git commit identity.
4. A SHA-256 checksum for the APK/AAB.
5. Release notes listing visible UI changes, data/API changes, and known limitations.
6. A retained previous APK and source baseline so rollback never depends on memory.

The installed application must package its UI assets. A WebView that only opens the live website is not considered a versioned release, because the interface could still change without a new APK.

## Required scope unlock

The current direction lock allows component, page, store, hook, utility, service, and documentation edits. A real Android package additionally requires permission to add or modify:

- `/web/android/`
- `/web/capacitor.config.*`
- `/web/package.json`
- `/web/package-lock.json`
- `/web/src/app/` for static/mobile bootstrapping where required
- `/scripts/` for repeatable release commands

Until those paths are explicitly allowed, the safe stopping point is the frozen baseline and architecture decision; no Android wrapper should be created outside the declared lock.

