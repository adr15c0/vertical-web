#!/usr/bin/env python3
"""
rest_wpcli_roundtrip.py — issue #9: REST <-> WP-CLI round-trip test.

Establishes (and asserts, empirically) the real responsibility boundary between
the WordPress REST API (Application Passwords — what the browser/BFF console can
use) and WP-CLI (server-side), for Divi Builder pages.

FINDING (verified by this test, correcting an earlier assumption):
  * REST *can* create/edit page content AND enable the Divi Builder. Divi
    registers `_et_pb_use_builder` (and `_et_pb_old_content`) for REST during
    `rest_api_init`, so an authenticated user with edit capability can set them
    via the `meta` field. (They are invisible to WP-CLI `get_registered_meta_keys`
    because that runs outside a REST request — which is why the CLI-era assumption
    that this meta was "unreachable via REST" was wrong.)
  * REST CANNOT set the remaining builder-provenance meta
    (`_et_pb_built_for_post_type`, `_et_builder_version`) — Divi does not expose
    those to REST — nor any site-level Divi OPTION (Global Colors, presets):
    core REST /settings doesn't include them. Those require WP-CLI (or a custom
    mu-plugin endpoint).

CONSEQUENCE for the console (#18): per-page content editing + builder enablement
is a pure-REST path; a thin server-side "finish/publish" step (WP-CLI) stamps the
provenance meta and owns site-level design tokens.

Flow (local DDEV site):
  Part 1 — REST owns content + builder enablement
    1. REST create a page with Divi shortcode content
    2. REST set `_et_pb_use_builder=on` -> assert it took (REST + WP-CLI agree)
    3. REST update content -> assert REST owns content
    4. verify raw shortcodes intact via REST (context=edit) AND WP-CLI
  Part 2 — the real WP-CLI-only boundary
    5. REST cannot set `_et_pb_built_for_post_type` -> WP-CLI sets it + version
    6. core REST /settings does not expose the `et_divi` option (Global Colors);
       WP-CLI can read it
  Then: log the run to the tooling DB job_log; revoke the temp App Password.

Idempotent: re-running replaces the fixed-slug test page. Local dev only
(TLS verification disabled against the mkcert cert).

Usage:  python3 scripts/local/rest_wpcli_roundtrip.py
"""
from __future__ import annotations

import base64
import json
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PG_CONTAINER = f"ddev-{REPO_ROOT.name}-postgres"
LOCAL_URL = "https://vertical-web.ddev.site"
REST = f"{LOCAL_URL}/wp-json/wp/v2"
ADMIN_ROLE = "administrator"
APP_PW_NAME = "rest-roundtrip-test"
TEST_SLUG = "rest-wpcli-roundtrip"
DIVI_VERSION = "4.27.7"
MARKER = "ROUNDTRIP_MARKER"


def divi_content(marker: str) -> str:
    """A minimal but real Divi Builder page (section/row/column/text)."""
    return (
        f'[et_pb_section fb_built="1" _builder_version="{DIVI_VERSION}"]'
        f'[et_pb_row _builder_version="{DIVI_VERSION}"]'
        f'[et_pb_column type="4_4" _builder_version="{DIVI_VERSION}"]'
        f'[et_pb_text _builder_version="{DIVI_VERSION}"]{marker}[/et_pb_text]'
        f'[/et_pb_column][/et_pb_row][/et_pb_section]'
    )


# --------------------------------------------------------------------------- #
# shells: WP-CLI (ddev wp) and psql (tooling DB)
# --------------------------------------------------------------------------- #
def wp(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["ddev", "wp", *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"ddev wp {' '.join(args[:3])}... failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def psql(sql: str, variables: dict[str, str] | None = None) -> None:
    cmd = ["docker", "exec", "-i", PG_CONTAINER, "psql", "-v", "ON_ERROR_STOP=1"]
    for k, v in (variables or {}).items():
        cmd += ["-v", f"{k}={v}"]
    cmd += ["-U", "tooling", "-d", "vertical_tooling"]
    proc = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"psql failed: {proc.stderr.strip()}")


# --------------------------------------------------------------------------- #
# REST (Application Passwords, local TLS verification off)
# --------------------------------------------------------------------------- #
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def rest(method: str, path: str, user: str, app_pw: str,
         body: dict | None = None) -> tuple[int, dict]:
    url = f"{REST}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    token = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


# --------------------------------------------------------------------------- #
def main() -> int:
    started = time.time()
    checks: list[tuple[str, bool, str]] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        checks.append((label, ok, detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

    admin = wp("user", "list", f"--role={ADMIN_ROLE}", "--field=user_login").splitlines()[0].strip()
    print(f"[setup] admin user: {admin}")

    for uuid in wp("user", "application-password", "list", admin,
                   f"--name={APP_PW_NAME}", "--field=uuid", check=False).split():
        wp("user", "application-password", "delete", admin, f"--uuid={uuid}", check=False)
    app_pw = wp("user", "application-password", "create", admin, APP_PW_NAME, "--porcelain")
    print("[setup] minted temporary Application Password")

    try:
        for pid in wp("post", "list", "--post_type=page", f"--name={TEST_SLUG}",
                      "--field=ID", check=False).split():
            wp("post", "delete", pid, "--force", check=False)

        # ---------- Part 1: REST owns content + builder enablement -------- #
        print("\n[1] REST create page ...")
        status, page = rest("POST", "/pages", admin, app_pw, {
            "title": "REST<->WP-CLI Round-trip",
            "slug": TEST_SLUG,
            "status": "publish",
            "content": divi_content(f"{MARKER}_V1"),
        })
        check("REST create returns 201", status == 201, f"HTTP {status}")
        page_id = int(page["id"])
        print(f"      page id: {page_id}")

        print("\n[2] REST sets _et_pb_use_builder=on (Divi exposes it to REST) ...")
        status, updated = rest("POST", f"/pages/{page_id}", admin, app_pw,
                               {"meta": {"_et_pb_use_builder": "on"}})
        rest_meta = updated.get("meta", {}).get("_et_pb_use_builder")
        cli_meta = wp("post", "meta", "get", str(page_id), "_et_pb_use_builder", check=False).strip()
        check("REST set _et_pb_use_builder=on", status == 200 and rest_meta == "on" and cli_meta == "on",
              f"HTTP {status}, rest='{rest_meta}', cli='{cli_meta}'")

        print("\n[3] REST update content ...")
        status, _ = rest("POST", f"/pages/{page_id}", admin, app_pw,
                         {"content": divi_content(f"{MARKER}_V2")})
        check("REST content update returns 200", status == 200, f"HTTP {status}")

        print("\n[4] Verify content round-trip (REST raw + WP-CLI) ...")
        _, edited = rest("GET", f"/pages/{page_id}?context=edit", admin, app_pw)
        raw = edited.get("content", {}).get("raw", "")
        check("REST raw content has updated marker", f"{MARKER}_V2" in raw)
        check("REST raw content preserved Divi shortcodes",
              "[et_pb_section" in raw and "[et_pb_text" in raw)
        cli_content = wp("post", "get", str(page_id), "--field=post_content")
        check("WP-CLI sees same shortcodes + marker",
              "[et_pb_section" in cli_content and f"{MARKER}_V2" in cli_content)

        # ---------- Part 2: the real WP-CLI-only boundary ----------------- #
        print("\n[5] REST cannot set provenance meta -> WP-CLI finishes it ...")
        rest("POST", f"/pages/{page_id}", admin, app_pw,
             {"meta": {"_et_pb_built_for_post_type": "page"}})
        after_rest = wp("post", "meta", "get", str(page_id), "_et_pb_built_for_post_type", check=False).strip()
        check("REST did NOT set _et_pb_built_for_post_type (not REST-exposed)", after_rest == "",
              f"cli='{after_rest}'")
        wp("post", "meta", "update", str(page_id), "_et_pb_built_for_post_type", "page")
        wp("post", "meta", "update", str(page_id), "_et_builder_version", f"BB|Divi|{DIVI_VERSION}")
        check("WP-CLI stamped provenance meta",
              wp("post", "meta", "get", str(page_id), "_et_pb_built_for_post_type").strip() == "page"
              and wp("post", "meta", "get", str(page_id), "_et_builder_version").strip() != "")

        print("\n[6] Site-level Divi option (Global Colors) is WP-CLI-only ...")
        _, sett = rest("GET", "/settings", admin, app_pw)
        check("core REST /settings does NOT expose et_divi option", "et_divi" not in sett)
        gc = wp("option", "get", "et_divi", "--format=json", check=False)
        check("WP-CLI can read the et_divi option", gc.strip() not in ("", "null"),
              "Global Colors live in the et_divi option")

        ok = all(passed for _, passed, _ in checks)
        elapsed_ms = int((time.time() - started) * 1000)

        ctx = {"page_id": page_id, "slug": TEST_SLUG,
               "checks": [{"label": l, "ok": p, "detail": d} for l, p, d in checks]}
        psql(
            "INSERT INTO job_log(job, status, duration_ms, context, message) VALUES "
            "('rest_wpcli_roundtrip', :'st', :dur, :'ctx'::jsonb, :'msg');",
            {"st": "success" if ok else "error", "dur": str(elapsed_ms),
             "ctx": json.dumps(ctx),
             "msg": f"{sum(p for _, p, _ in checks)}/{len(checks)} checks passed"},
        )

        vb_url = f"{LOCAL_URL}/?page_id={page_id}&et_fb=1&PageSpeed=off"
        print("\n" + ("All checks passed." if ok else "SOME CHECKS FAILED."))
        print(f"  Test page id:   {page_id}")
        print(f"  Visual Builder: {vb_url}")
        print(f"  Logged to job_log ({elapsed_ms} ms).")
        return 0 if ok else 1
    finally:
        for uuid in wp("user", "application-password", "list", admin,
                       f"--name={APP_PW_NAME}", "--field=uuid", check=False).split():
            wp("user", "application-password", "delete", admin, f"--uuid={uuid}", check=False)
        print("[cleanup] revoked temporary Application Password")


if __name__ == "__main__":
    sys.exit(main())
