#!/usr/bin/env python3
"""
push_hero_card.py — Divi asset pipeline POC pusher (issue #8).

Generates the hero+card asset (asset-pipeline/generators/hero_card.py), writes the
Divi Library portability JSON, and pushes everything to the local WordPress via
**WP-CLI** (which bypasses the 2 MB REST/upload limit):

  * Global Colors  -> wp option patch update et_divi et_global_colors
  * Module preset  -> merged into et_divi_builder_global_presets_ng
  * Library layout -> et_pb_layout post (+ layout_type/scope terms)
  * Demo page      -> a page built from the layout, editable in the Visual Builder

It then registers the asset in the Postgres tooling DB (divi_assets + asset_versions)
and logs to job_log. Prints the Visual Builder URL to verify.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = Path(__file__).resolve().parent / "generators"
OUT_DIR = Path(__file__).resolve().parent / "out"
PG_CONTAINER = f"ddev-{REPO_ROOT.name}-postgres"
LOCAL_URL = "https://vertical-web.ddev.site"

sys.path.insert(0, str(GEN_DIR))
import hero_card  # noqa: E402


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


def ensure_term(taxonomy: str, term: str) -> None:
    # Create the term if missing (ignore "already exists"); then it can be set.
    subprocess.run(["ddev", "wp", "term", "create", taxonomy, term, f"--slug={term}"],
                   cwd=REPO_ROOT, capture_output=True, text=True)


def main() -> int:
    bundle = hero_card.generate()
    shortcodes = bundle["shortcodes"]
    preset_id = bundle["preset_id"]
    portability = bundle["portability_json"]

    print("[1/6] Writing portability JSON ...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "hero-card.layout.json"
    out_json.write_text(json.dumps(portability, indent=2))

    print("[2/6] Pushing Global Colors (wp option patch) ...")
    gc_payload = {gcid: {"color": hexv, "active": "yes"}
                  for gcid, hexv in bundle["global_colors"].items()}
    wp("option", "patch", "update", "et_divi", "et_global_colors",
       json.dumps(gc_payload), "--format=json")

    print("[3/6] Merging module preset into global presets ...")
    presets = json.loads(wp("option", "get", "et_divi_builder_global_presets_ng",
                            "--format=json"))
    btn = presets.setdefault("et_pb_button", {"default": "_initial", "presets": {}})
    btn.setdefault("presets", {})[preset_id] = bundle["preset"]
    wp("option", "update", "et_divi_builder_global_presets_ng",
       json.dumps(presets), "--format=json")

    print("[4/6] Creating Divi Library layout (et_pb_layout) via WP-CLI ...")
    layout_id = wp("post", "create", "--post_type=et_pb_layout", "--post_status=publish",
                   f"--post_title={bundle['title']}", f"--post_content={shortcodes}",
                   "--porcelain")
    for tax, term in (("layout_type", "layout"), ("scope", "not_global"),
                      ("module_width", "regular")):
        ensure_term(tax, term)
        wp("post", "term", "set", layout_id, tax, term)
    wp("post", "meta", "update", layout_id, "_et_pb_built_for_post_type", "page")

    print("[5/6] Creating demo page (editable in Visual Builder) ...")
    page_id = wp("post", "create", "--post_type=page", "--post_status=publish",
                 "--post_title=POC Landing (generated)",
                 f"--post_content={shortcodes}", "--porcelain")
    wp("post", "meta", "update", page_id, "_et_pb_use_builder", "on")
    wp("post", "meta", "update", page_id, "_et_pb_built_for_post_type", "page")
    wp("post", "meta", "update", page_id, "_et_builder_version", f"BB|Divi|{hero_card.BUILDER_VERSION}")

    print("[6/6] Registering asset in tooling DB (divi_assets + asset_versions) ...")
    content_json = json.dumps(portability)
    checksum = hashlib.sha256(content_json.encode()).hexdigest()
    meta = json.dumps({"library_post_id": int(layout_id), "demo_page_id": int(page_id),
                       "preset_id": preset_id, "modules": "core-only",
                       "global_colors": len(bundle["global_colors"])})
    psql(
        """
        WITH up AS (
          INSERT INTO divi_assets(asset_key, asset_type, title, language, wp_post_id,
                                  source, status, current_version, metadata)
          VALUES ('poc-hero-card','library_layout', :'title','en', :wp_post_id,
                  'generated','active',1, :'meta'::jsonb)
          ON CONFLICT (asset_key) DO UPDATE
            SET wp_post_id=EXCLUDED.wp_post_id, title=EXCLUDED.title,
                metadata=EXCLUDED.metadata, current_version=1, status='active',
                updated_at=now()
          RETURNING id
        )
        INSERT INTO asset_versions(asset_id, version, content, content_format,
                                   checksum, created_by)
        SELECT id, 1, :'content'::jsonb, 'divi_layout_json', :'checksum',
               'asset_pipeline_push' FROM up
        ON CONFLICT (asset_id, version) DO UPDATE
          SET content=EXCLUDED.content, checksum=EXCLUDED.checksum;
        """,
        {"title": bundle["title"], "wp_post_id": layout_id, "meta": meta,
         "content": content_json, "checksum": checksum},
    )
    psql(
        "INSERT INTO job_log(job, status, context) VALUES "
        "('asset_pipeline_push','success', :'ctx'::jsonb);",
        {"ctx": json.dumps({"asset_key": "poc-hero-card", "library_post_id": int(layout_id),
                            "demo_page_id": int(page_id), "preset_id": preset_id})},
    )

    vb_url = f"{LOCAL_URL}/?page_id={page_id}&et_fb=1&PageSpeed=off"
    print("\nDone.")
    print(f"  Library layout post: {layout_id} (et_pb_layout)")
    print(f"  Demo page:           {page_id}")
    print(f"  Portability JSON:    {out_json.relative_to(REPO_ROOT)}")
    print(f"  Preset id:           {preset_id}")
    print(f"  Open in Visual Builder: {vb_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
