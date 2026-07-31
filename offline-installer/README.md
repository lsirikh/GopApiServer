# GOP API Server — Offline One-Click Installer

Upgrade an **air-gapped** GOP API Server site (running **v6.0+**, PostgreSQL era) to the latest version
with a single `.exe`, **without ever losing the DB or runtime data**.

> Why an image bundle (not git): the `Dockerfile` builds via `apt`/`pip`/`playwright` — all need internet.
> On an air-gapped host `docker compose up --build` cannot work, so we carry pre-built images instead.
> App code rides inside the image (`COPY . .`); on the host only `docker-compose.yml` needs refreshing,
> while `.env` / `data` / `certs` / named volumes are preserved.

## Layout

```
offline-installer/
  build/
    make-offline-bundle.ps1   # office PC: build + docker save + payload  -> dist/bundle
    installer.iss             # Inno Setup: wrap dist/bundle into one .exe
  installer/
    install.ps1               # orchestrator (-Silent / -Rollback / -Rehearse)
    preserve.list             # host paths never overwritten
    lib/*.ps1                 # detect / snapshot / preflight / backup / sync / apply / verify / rollback / rehearse
    tests/*.ps1               # unit tests + rehearsal drill
```

## Workflow

**1. Office (internet):**
```powershell
powershell -File offline-installer\build\make-offline-bundle.ps1
# then compile installer.iss with Inno Setup (ISCC) -> dist\gop_offline_installer_v6.3.0.exe
```
Copy the `.exe` to USB.

**2. Before the trip — REHEARSE (proves rollback, real project untouched):**
```powershell
powershell -ExecutionPolicy Bypass -File offline-installer\installer\install.ps1 -Rehearse -RepoDir "C:\workspace_python\api-test-server"
```
Clones the real volume read-only into an isolated sandbox, runs upgrade→forced-failure→auto-rollback,
asserts identical restore, tears the sandbox down. Your live stack keeps running.

**3. On site (air-gapped):** double-click the `.exe`. It elevates, extracts, and runs unattended:
`preflight → backup(+integrity gate) → [point of no return] → load+up → verify → (fail ⇒ auto-rollback)`.

**Manual rollback** (if ever needed):
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Rollback -RepoDir "<target repo>"
```

## Safety guarantees

- **DB never deleted**: named volume survives `down` (never `-v`). Project name is **detected from the
  running postgres mount and pinned** (`COMPOSE_PROJECT_NAME`) so compose binds the existing volume.
- **Precise rollback**: physical volume snapshot (proven round-trip) + `pg_dump` + image `:rollback` tags
  + config snapshots. Failure after the point-of-no-return auto-restores all three layers.
- **Assumption-safe**: preflight validates volume/network/version at runtime; mismatch aborts *before* any change.

See `docs/RUNBOOK_offline_installer.md` and `docs/RUNBOOK_offline_installer_rollback.md`.
