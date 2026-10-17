# Repository security cleanup plan (NEMT App V0.1)

Date: 2026-10-17
Status: **findings confirmed; no destructive action taken**.

This document records repository hygiene findings required by issue #6. Secret
values were not copied into this document, logs or any new file.

## Findings

| Severity | Path | Finding |
|---|---|---|
| **Critical** | `cos_sync.env` | Tracked file containing keys named `COS_SECRET_ID` and `COS_SECRET_KEY` (Tencent COS credentials). |
| **Critical** | `ssh_key_nemt` | Tracked SSH **private key** (PEM header). |
| High | `node_modules/` | ~35,308 tracked dependency files, including `app-builder-lib/certs/root_certs.keychain`; tracked artifacts make secret scanning and upgrades unreliable. |
| Medium | history | Removing files from the working tree does not remove them from Git history or GitHub caches. |
| **Critical** | `ssh_connect.py`, `ssh_setup_server.py`, `ssh_quick_test.py`, `ssh_install_tools.py`, `ssh_passwordless_setup.py`, `ssh_fix_apt.py`, `ssh_install_nodejs*.py` | Tracked one-off scripts contain hard-coded SSH server credentials. These target the legacy server and must be rotated; values are not repeated here. |
| High | deployment access | The server root password was shared in chat. SSH password auth is disabled (publickey only), and access was performed with an existing authorized key. Rotate the console/root password if it is used elsewhere. |

The demo/test values in `backend/.env.example`, tests and the DEMO login hint
are intentional placeholders and are not real credentials.

## Immediate actions (owner, outside this code change)

1. **Rotate** the Tencent COS SecretId/SecretKey and delete/disable the old
   key pair in the cloud console. Audit COS access logs for abuse.
2. **Revoke** the SSH key (`ssh_key_nemt.pub` identifies the key) on every
   server/account where it is authorized. Generate a new key pair and update
   access.
3. If the repository is public or has been shared, assume exposure. Check
   GitHub secret scanning alerts and any forks/caches.
4. Do not paste credentials into issues, chat or pull requests. Store new
   values in a secret manager or the deployment environment only.
5. Rotate the legacy server credentials referenced by the tracked `ssh_*.py`
   scripts (and remove/replace those literals in a separate approved change).
6. Rotate any console/root password shared during deployment; prefer SSH keys
   and a non-root deploy account.

## Git cleanup plan (requires owner approval)

A history rewrite is destructive and must be scheduled with all collaborators:

1. Freeze merges to the affected branches and inform collaborators.
2. Rotate all exposed credentials **first**; history cleanup does not secure an
   already-leaked key.
3. Remove the files from the index in a dedicated commit (this stops future
   exposure but leaves history):
   ```bash
   git rm --cached cos_sync.env ssh_key_nemt ssh_key_nemt.pub
   # dependencies, in a separate commit:
   git rm -r --cached node_modules NEMT-Simulator2/web/node_modules
   ```
4. Rewrite history to purge the blobs (example, after review and backup):
   ```bash
   git filter-repo --path cos_sync.env \
     --path ssh_key_nemt --path ssh_key_nemt.pub --invert-paths
   ```
   Coordinate a force-push, re-clone, and re-open/refresh PRs. GitHub support
   may be required to garbage-collect cached views/forks.
5. Add/keep ignores: `.env*` (except examples), `cos_sync.env`,
   `ssh_key_*`, `*.pem`, `*.key`, `*.keychain`, `node_modules/`, `.next/`,
   `dist/`, `build/`.
6. Enable GitHub secret scanning + push protection and a CI secret scan after
   history is clean. A scanner is intentionally **not** enabled yet because it
   would fail immediately on the known history.
7. Document the new server-side secret provisioning and do a dependency
   audit (`npm audit`, `pip-audit`) in a follow-up PR.

## Already applied in this change

- Added `.env*`-style ignore rules with `.env.example` exceptions.
- Added ignores for `cos_sync.env`, `ssh_key_nemt*`, `*.keychain`,
  `node_modules/`, `.next/`, and SQLite WAL files.
- Bound `quant-mvp` Redis and Redis Commander to `127.0.0.1`.
- The app API keeps secrets server-side and requires templates/placeholders in
  `.env.example`; tests use obvious dummy values only.

## Deliberately not done

- No history rewrite, force-push or deletion of the tracked secret files.
- No removal of the 35k tracked dependency files from the index.
- No claim that rotating credentials is complete; that must be performed and
  recorded by the owner.
