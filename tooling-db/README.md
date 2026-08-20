# Tooling DB

The project's own **Postgres** store (separate from the operational **Vertical DB**).
It holds the Divi asset registry + versions, AI translation drafts with human-review
state, inventory snapshots, and a job/audit log. Uses Postgres for **Azure parity** —
production runs on Azure Database for PostgreSQL.

## Run it (local)

Postgres runs as a DDEV add-on service (`.ddev/docker-compose.postgres.yaml`):

```bash
ddev restart                       # starts the postgres service; schema v0 auto-applies on first init
scripts/local/tooling_db.sh status # tables + row counts + applied migrations
scripts/local/tooling_db.sh psql   # interactive shell
scripts/local/tooling_db.sh migrate  # re-apply migrations (idempotent)
```

## Connection (local dev creds only — never used in prod)

| From | Host | Port | DB | User | Password |
|---|---|---|---|---|---|
| DDEV web container | `postgres` | 5432 | `vertical_tooling` | `tooling` | `tooling` |
| macOS host (psql/DBeaver/console) | `127.0.0.1` | 5433 | `vertical_tooling` | `tooling` | `tooling` |

Production credentials come from **Azure Key Vault** and are never committed.

## Schema v0 (`migrations/0001_init.sql`)

| Table | Purpose |
|---|---|
| `divi_assets` | Registry of managed Divi assets (Library layouts, presets, Theme Builder templates, Global Colors, page layouts). |
| `asset_versions` | Immutable content versions per asset (Divi JSON / shortcode / preset / global-colors payload). |
| `translation_drafts` | AI drafts + human-review state per field/segment; `diverged` guards intentional EN/ES divergence. |
| `inventory_snapshots` | Point-in-time inventory captures (e.g. `divi_recon`). |
| `job_log` | Audit/job log for pipeline + refresh operations. |

Migrations are idempotent (`CREATE TABLE IF NOT EXISTS`, etc.) and safe to re-run.
