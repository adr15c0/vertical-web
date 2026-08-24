# console

The **internal admin console** — a React app on the WordPress REST API for **non-developer staff**.

Scope (intentionally narrow):
- Edit **content/data** (pages, CPT entries), swap media.
- Browse the **Divi asset library** (from the Postgres tooling DB).
- **Translation queue**: review AI-drafted translations (Phase 3).

Out of scope: building layouts. **Layout/design stays in the Divi Visual Builder.** The console must
not try to reinvent Divi's builder.

Backends: WordPress REST API (content) + Postgres tooling DB (asset registry, translation drafts,
audit log). Local-only hosting for now; production hosting decided during the Azure build (Phase 4).

## v0 (this build — issues #17 + #19)

A **dashboard** (asset/version/inventory/job counts, latest inventory snapshot, recent pipeline jobs)
and a **Divi asset library browser** (the `divi_assets` registry + version history). Read-only.

```
React/MUI SPA  ──/api──▶  FastAPI BFF  ──▶  Postgres tooling DB (assets, jobs, inventory)
(console/web)             (console/api)  └─▶  WordPress REST (Application Passwords)
```

A browser can't reach Postgres or WP-CLI directly, so the BFF is the bridge.

### Run locally

Prereq: DDEV up (`ddev start`) so the tooling DB is on `127.0.0.1:5433`.

```bash
# BFF (FastAPI)
cd console/api
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8787

# Front-end (React/MUI)
cd console/web && npm install && npm run dev   # http://localhost:5173 (proxies /api)
```

Or single-origin: `npm run build` in `console/web`, then open the BFF at `http://127.0.0.1:8787/`
(it serves the built SPA). BFF routes: `/api/health` `/api/summary` `/api/assets` `/api/assets/{key}`
`/api/inventory` `/api/jobs` `/api/wp/pages`.

Local dev credentials only; production creds come from Azure Key Vault. `.venv/`, `node_modules/`,
`dist/`, `.env` are git-ignored.

