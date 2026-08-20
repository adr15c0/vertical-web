#!/usr/bin/env python3
"""
REST inventory of a live WordPress site (read-only).

Pulls pages, posts, and media via the WP REST API using an Application Password,
capturing raw Divi shortcode content (context=edit). Writes JSON to an output
directory and prints a summary. No writes are made to the source site.

Config comes from the repo-root .env:
  SOURCE_WP_URL, SOURCE_WP_APP_USER, SOURCE_WP_APP_PASSWORD

Usage:
  python3 scripts/local/rest_inventory.py [--out DIR]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "backups" / "en" / "inventory"


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.split("#", 1)[0].strip()  # strip trailing inline comment
        env[key.strip()] = val
    return env


def auth_header(user: str, app_password: str) -> str:
    # WordPress accepts the application password with or without spaces.
    token = base64.b64encode(f"{user}:{app_password.replace(' ', '')}".encode()).decode()
    return f"Basic {token}"


TIMEOUT = 120
RETRIES = 3


def fetch(url: str, headers: dict, ctx: ssl.SSLContext):
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            return urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
        except urllib.error.HTTPError:
            raise  # HTTP errors are meaningful; don't retry blindly
        except Exception as e:  # timeouts, resets
            last = e
            if attempt < RETRIES:
                print(f"    retry {attempt}/{RETRIES - 1} after: {type(e).__name__}", flush=True)
    raise last  # type: ignore[misc]


def collect(base: str, endpoint: str, headers: dict, ctx: ssl.SSLContext, per_page: int = 25) -> list:
    """Paginate an endpoint (context=edit) and return all items."""
    items: list = []
    page = 1
    while True:
        url = f"{base}/wp-json/wp/v2/{endpoint}?per_page={per_page}&page={page}&context=edit"
        try:
            resp = fetch(url, headers, ctx)
        except urllib.error.HTTPError as e:
            # page beyond last returns 400 with code rest_post_invalid_page_number
            if e.code in (400,) and page > 1:
                break
            raise
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1") or "1")
        batch = json.loads(resp.read().decode())
        if not batch:
            break
        items.extend(batch)
        if page >= total_pages:
            break
        page += 1
    return items


def divi_count(items: list) -> int:
    n = 0
    for it in items:
        raw = ""
        c = it.get("content")
        if isinstance(c, dict):
            raw = c.get("raw") or c.get("rendered") or ""
        if "[et_pb_section" in raw:
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    env = load_env(REPO_ROOT / ".env")
    base = (env.get("SOURCE_WP_URL") or "").rstrip("/")
    user = env.get("SOURCE_WP_APP_USER") or ""
    pw = env.get("SOURCE_WP_APP_PASSWORD") or ""
    if not (base and user and pw):
        print("ERROR: SOURCE_WP_URL / SOURCE_WP_APP_USER / SOURCE_WP_APP_PASSWORD must be set in .env")
        return 2

    headers = {"Authorization": auth_header(user, pw), "User-Agent": "vertical-web-inventory/1.0"}
    ctx = ssl.create_default_context()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Source: {base}  (user: {user})")

    # Sanity check auth against /users/me
    try:
        me = json.loads(fetch(f"{base}/wp-json/wp/v2/users/me?context=edit", headers, ctx).read().decode())
        print(f"Authenticated as: {me.get('name')} (id {me.get('id')}, roles {me.get('roles')})")
    except urllib.error.HTTPError as e:
        print(f"AUTH FAILED ({e.code}): {e.read().decode()[:200]}")
        return 1

    summary = {}
    for endpoint in ("pages", "posts"):
        print(f"Fetching {endpoint} ...", flush=True)
        items = collect(base, endpoint, headers, ctx)
        (out / f"{endpoint}.json").write_text(json.dumps(items, indent=2))
        entry = {"count": len(items), "divi_built": divi_count(items)}
        summary[endpoint] = entry
        print(f"  {endpoint}: {entry}")

    # media: count only (full media is already in the uploads backup)
    print("Counting media ...", flush=True)
    try:
        resp = fetch(f"{base}/wp-json/wp/v2/media?per_page=1&context=edit", headers, ctx)
        summary["media"] = {"count": int(resp.headers.get("X-WP-Total", "0") or "0")}
    except Exception as e:
        summary["media"] = {"count": None, "error": str(e)[:120]}
    print(f"  media: {summary['media']}")

    # REST namespaces (plugin fingerprints)
    try:
        root = json.loads(fetch(f"{base}/wp-json/", headers, ctx).read().decode())
        summary["namespaces"] = root.get("namespaces", [])
    except Exception:
        summary["namespaces"] = []

    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
