"""
main.py — console BFF (FastAPI).

Read-only v0 surface over the tooling DB (Divi asset registry, inventory
snapshots, job log) plus a WordPress REST proxy for pages. This is the backend
the React/MUI console talks to; a browser can't reach Postgres or WP-CLI directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import db
from config import settings

app = FastAPI(title="Vertical Console BFF", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings()["cors_origins"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Health + summary
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "db": "ok" if db.ping() else "down"}


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    counts = db.query_one(
        """
        SELECT
          (SELECT count(*) FROM divi_assets)         AS assets,
          (SELECT count(*) FROM asset_versions)      AS asset_versions,
          (SELECT count(*) FROM inventory_snapshots) AS inventory_snapshots,
          (SELECT count(*) FROM job_log)             AS jobs;
        """
    ) or {}
    latest_job = db.query_one(
        "SELECT id, job, status, ran_at, duration_ms FROM job_log "
        "ORDER BY ran_at DESC LIMIT 1;"
    )
    latest_inventory = db.query_one(
        "SELECT id, taken_at, environment, site, kind, summary "
        "FROM inventory_snapshots ORDER BY taken_at DESC LIMIT 1;"
    )
    return {
        "counts": counts,
        "latest_job": latest_job,
        "latest_inventory": latest_inventory,
    }


# --------------------------------------------------------------------------- #
# Divi asset registry (#19)
# --------------------------------------------------------------------------- #
@app.get("/api/assets")
def assets() -> list[dict[str, Any]]:
    return db.query(
        """
        SELECT asset_key, asset_type, title, language, status, source,
               wp_post_id, current_version, updated_at
        FROM divi_assets
        ORDER BY updated_at DESC;
        """
    )


@app.get("/api/assets/{asset_key}")
def asset_detail(asset_key: str) -> dict[str, Any]:
    asset = db.query_one(
        "SELECT * FROM divi_assets WHERE asset_key = %s;", (asset_key,)
    )
    if not asset:
        raise HTTPException(status_code=404, detail="asset not found")
    versions = db.query(
        """
        SELECT version, content_format, checksum, created_by, created_at
        FROM asset_versions
        WHERE asset_id = %s
        ORDER BY version DESC;
        """,
        (asset["id"],),
    )
    return {"asset": asset, "versions": versions}


# --------------------------------------------------------------------------- #
# Inventory snapshots + job log (#17 dashboard)
# --------------------------------------------------------------------------- #
@app.get("/api/inventory")
def inventory(limit: int = 20) -> list[dict[str, Any]]:
    return db.query(
        "SELECT id, taken_at, environment, site, kind, summary, artifact_path "
        "FROM inventory_snapshots ORDER BY taken_at DESC LIMIT %s;",
        (limit,),
    )


@app.get("/api/jobs")
def jobs(limit: int = 30) -> list[dict[str, Any]]:
    return db.query(
        "SELECT id, job, status, ran_at, duration_ms, message, error "
        "FROM job_log ORDER BY ran_at DESC LIMIT %s;",
        (limit,),
    )


# --------------------------------------------------------------------------- #
# WordPress REST proxy (read-only pages list)
# --------------------------------------------------------------------------- #
@app.get("/api/wp/pages")
def wp_pages() -> list[dict[str, Any]]:
    wp = settings()["wp"]
    if not wp["user"] or not wp["app_password"]:
        # No creds configured — return empty rather than error (dashboard still loads).
        return []
    url = f"{wp['base_url'].rstrip('/')}/wp-json/wp/v2/pages"
    try:
        resp = httpx.get(
            url,
            params={"per_page": 50, "status": "publish", "_fields": "id,title,link,modified"},
            auth=(wp["user"], wp["app_password"]),
            verify=wp["verify_tls"],
            timeout=15,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"WordPress REST error: {e}")
    return [
        {"id": p["id"], "title": p.get("title", {}).get("rendered", ""),
         "link": p.get("link"), "modified": p.get("modified")}
        for p in resp.json()
    ]


# --------------------------------------------------------------------------- #
# Serve the built React SPA (console/web/dist) if present, so a single origin
# serves both the UI and /api. Mounted last so /api/* routes take precedence.
# --------------------------------------------------------------------------- #
_dist = Path(__file__).resolve().parents[1] / "web" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="spa")
