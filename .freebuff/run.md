# CrimeGraph AI — Run Instructions

## Architecture
- **Frontend**: React + Vite + Cytoscape.js + Recharts
- **Backend**: FastAPI + Python + spaCy NER + NetworkX
- **Database**: PostgreSQL 16 (5432) + Neo4j 5 (7687) — optional; the app degrades to in-memory mode without them

## Ports (updated 2026-10-12)

The documented defaults (frontend 3000, backend 8000) were **occupied on this
machine**: 8000 by another project (`python -m qscope`) and 3000 by a stale,
unresponsive vite process. Current working ports:

| Service  | Port | Notes |
|----------|------|-------|
| Backend  | **8010** | uvicorn, 127.0.0.1 |
| Frontend | **3100** | vite `--strictPort` |

Check availability before starting: `netstat -ano | findstr :8010` (and `:3100`).
If the defaults are free again you may use 8000/3000 — the vite proxy reads
`API_TARGET` (see below), so only flags/env need changing.

## Reproduce uncommitted artifacts

Workspace == main checkout here, so there is **nothing to copy**:
- `.env` lives at `crime-network-prototype/.env` (committed to this workspace)
  with `DATABASE_URL`, `NEO4J_*`, `CORS_ORIGINS`. Procedures only — do not
  record values. If starting from a fresh clone, copy `.env` from the main
  checkout.
- Python deps (system Python 3.14, already installed):
  `pip install fastapi "uvicorn[standard]" pydantic python-dotenv "sqlalchemy[asyncio]" asyncpg neo4j spacy networkx aiofiles python-multipart httpx`
  then `python -m spacy download en_core_web_sm` (verified present).
  Note: `backend/requirements.txt` pins older versions (spacy 3.7.5 etc.) that
  do not build on Python 3.14 — the unpinned install above is what actually runs.
- Frontend deps: `cd crime-network-prototype/frontend && npm install`
  (`node_modules` + `package-lock.json` present; vite 6.4.3).

## Run the servers

Backend (from `crime-network-prototype/` so `backend.` imports and `.env` resolve):
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```
Expected warnings without PostgreSQL/Neo4j: `PostgreSQL init failed (will use
in-memory only)` and Neo4j connection errors — this is normal. The graph is
in-memory and starts empty; paste a report in Case Intake or `POST /api/load-cases`.

Frontend (from `crime-network-prototype/frontend/`):
```bash
API_TARGET=http://127.0.0.1:8010 npm run dev -- --host 0.0.0.0 --port 3100 --strictPort
```
- `API_TARGET` (added to `vite.config.js`) sets the `/api` proxy target.
  Defaults to `http://localhost:8000` when unset.
- Vite proxies `/api/*` to the backend; the app itself uses relative `/api` paths.

## Detached launch (Windows, for Freebuff preview)

stdout and stderr MUST go to different files (PowerShell fails otherwise), and
`$p` must be escaped as `\$p` when the command is passed through bash.
The `Start-Process` call may time out the calling shell on pipe handles — the
process usually started fine; check the log files and `Get-NetTCPConnection`.

Backend:
```powershell
powershell -NoProfile -Command "\$p = Start-Process -FilePath 'python.exe' -ArgumentList '-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8010' -WorkingDirectory '<root>\crime-network-prototype' -RedirectStandardOutput '<root>\.freebuff\backend-<id>.log' -RedirectStandardError '<root>\.freebuff\backend-<id>.log.err' -WindowStyle Hidden -PassThru; Write-Output \$p.Id"
```

Frontend (sets API_TARGET for the child process via `$env:`):
```powershell
powershell -NoProfile -Command "\$env:API_TARGET='http://127.0.0.1:8010'; \$p = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev','--','--host','0.0.0.0','--port','3100','--strictPort' -WorkingDirectory '<root>\crime-network-prototype\frontend' -RedirectStandardOutput '<root>\.freebuff\preview-<id>.log' -RedirectStandardError '<root>\.freebuff\preview-<id>.log.err' -WindowStyle Hidden -PassThru; Write-Output ('PID=' + \$p.Id)"
```

Then verify before registering:
```bash
curl http://127.0.0.1:8010/health          # {"status":"healthy",...}
curl http://localhost:3100/api/stats        # JSON stats (proxied)
```

## Access Points
- Frontend: http://localhost:3100
- Backend API: http://localhost:8010
- API Docs: http://localhost:8010/docs

## Known quirks
- `data/cases.json` is `[]` — no demo data ships; the graph starts empty.
- Console shows a benign cytoscape warning about custom wheel sensitivity.
- Ports 5173/4173/8080/8081 on this machine belong to other projects.
