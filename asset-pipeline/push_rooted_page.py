#!/usr/bin/env python3
"""
push_rooted_page.py — generate the "Rooted" page and publish it via WP-CLI.

Creates a Divi-built page (editable in the Visual Builder) from
asset-pipeline/generators/rooted_page.py, based on the "You Said Yes" design.
Idempotent: replaces an existing page with slug 'rooted'. Registers the asset in
the tooling DB (divi_assets + asset_versions) and logs to job_log.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = Path(__file__).resolve().parent / "generators"
PG_CONTAINER = f"ddev-{REPO_ROOT.name}-postgres"
LOCAL_URL = "https://vertical-web.ddev.site"
BUILDER_VERSION = "4.27.7"

sys.path.insert(0, str(GEN_DIR))
import rooted_page  # noqa: E402


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


def main() -> int:
    bundle = rooted_page.generate()
    shortcodes = bundle["shortcodes"]

    print("[1/4] Removing any prior 'Rooted' page + freeing the /rooted/ slug ...")
    pages = json.loads(wp("post", "list", "--post_type=page",
                          "--fields=ID,post_title", "--format=json", check=False) or "[]")
    for p in pages:
        if p.get("post_title") == "Rooted":
            wp("post", "delete", str(p["ID"]), "--force", check=False)
    # A non-page object (e.g. an attachment) may already own the 'rooted' slug,
    # which would push our page to 'rooted-2'. Rename any such holder.
    holders = json.loads(wp("post", "list", "--post_type=any", "--name=rooted",
                            "--fields=ID,post_type", "--format=json", check=False) or "[]")
    for h in holders:
        wp("post", "update", str(h["ID"]),
           f"--post_name=rooted-{h['post_type']}", check=False)

    print("[2/4] Creating the Rooted page via WP-CLI ...")
    page_id = wp("post", "create", "--post_type=page", "--post_status=publish",
                 "--post_title=Rooted", "--post_name=rooted",
                 f"--post_content={shortcodes}", "--porcelain")
    wp("post", "meta", "update", page_id, "_et_pb_use_builder", "on")
    wp("post", "meta", "update", page_id, "_et_pb_built_for_post_type", "page")
    wp("post", "meta", "update", page_id, "_et_builder_version",
       f"BB|Divi|{BUILDER_VERSION}")
    # Ensure the clean slug + refresh rewrite rules.
    wp("post", "update", page_id, "--post_name=rooted", check=False)
    wp("rewrite", "flush", check=False)

    print("[3/4] Registering asset in tooling DB ...")
    content = json.dumps({"format": "divi_page", "based_on": bundle["based_on"],
                          "shortcodes": shortcodes})
    checksum = hashlib.sha256(content.encode()).hexdigest()
    meta = json.dumps({"page_id": int(page_id), "slug": "rooted",
                       "based_on_page_id": bundle["based_on"]["page_id"]})
    psql(
        """
        WITH up AS (
          INSERT INTO divi_assets(asset_key, asset_type, title, language, wp_post_id,
                                  source, status, current_version, metadata)
          VALUES ('rooted-page','page_layout','Rooted','en', :wp_post_id,
                  'generated','active',1, :'meta'::jsonb)
          ON CONFLICT (asset_key) DO UPDATE
            SET wp_post_id=EXCLUDED.wp_post_id, metadata=EXCLUDED.metadata,
                current_version=1, status='active', updated_at=now()
          RETURNING id
        )
        INSERT INTO asset_versions(asset_id, version, content, content_format,
                                   checksum, created_by)
        SELECT id, 1, :'content'::jsonb, 'shortcode', :'checksum', 'push_rooted_page'
        FROM up
        ON CONFLICT (asset_id, version) DO UPDATE
          SET content=EXCLUDED.content, checksum=EXCLUDED.checksum;
        """,
        {"wp_post_id": page_id, "meta": meta, "content": content, "checksum": checksum},
    )
    psql("INSERT INTO job_log(job, status, context) VALUES "
         "('push_rooted_page','success', :'ctx'::jsonb);",
         {"ctx": json.dumps({"page_id": int(page_id), "slug": "rooted"})})

    print("[4/4] Done.")
    slug = wp("post", "get", page_id, "--field=post_name", check=False) or "rooted"
    print(f"  Page:  {LOCAL_URL}/{slug}/  (id {page_id})")
    print(f"  Visual Builder: {LOCAL_URL}/?page_id={page_id}&et_fb=1&PageSpeed=off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
