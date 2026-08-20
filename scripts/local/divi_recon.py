#!/usr/bin/env python3
"""
divi_recon.py — Local Divi reconnaissance for the English POC.

Runs against the live DDEV WordPress replica (via `ddev wp`) and produces:
  * A WP-CLI capability checklist (issue #10)
  * A Divi module dependency catalog — core vs third-party, with the pages that
    use each third-party module (issue #5)
  * An inventory of Divi Library items, Theme Builder templates, and Global
    Colors / global presets (issue #7)

Outputs:
  * backups/en/inventory/divi_recon.json   (machine-readable, git-ignored)
  * docs/reference/divi-module-catalog.md  (committed, human-readable deliverable)

Read-only. No changes are made to the local site.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = REPO_ROOT / "backups" / "en" / "inventory" / "divi_recon.json"
OUT_MD = REPO_ROOT / "docs" / "reference" / "divi-module-catalog.md"

# Structural Divi shortcodes are containers, not "modules" a designer drops in.
STRUCTURAL = {
    "et_pb_section",
    "et_pb_row",
    "et_pb_row_inner",
    "et_pb_column",
    "et_pb_column_inner",
}


def wp(*args: str, check: bool = True) -> str:
    """Run `ddev wp ...` and return stdout (stripped)."""
    proc = subprocess.run(
        ["ddev", "wp", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"ddev wp {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def db(query: str) -> str:
    return wp("db", "query", query, "--skip-column-names")


# --------------------------------------------------------------------------- #
# Section 1 — WP-CLI capability checklist (#10)
# --------------------------------------------------------------------------- #
def capability_checklist() -> list[dict]:
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    try:
        record("core version", True, wp("core", "version"))
    except Exception as e:  # noqa: BLE001
        record("core version", False, str(e))

    try:
        n = wp("plugin", "list", "--format=count")
        record("plugin list", True, f"{n} plugins")
    except Exception as e:  # noqa: BLE001
        record("plugin list", False, str(e))

    try:
        n = wp("theme", "list", "--format=count")
        record("theme list", True, f"{n} themes")
    except Exception as e:  # noqa: BLE001
        record("theme list", False, str(e))

    try:
        wp("db", "export", "/tmp/divi_recon_captest.sql", "--quiet")
        size = wp("eval", "echo filesize('/tmp/divi_recon_captest.sql');")
        wp("eval", "@unlink('/tmp/divi_recon_captest.sql');")
        record("db export", True, f"{size} bytes")
    except Exception as e:  # noqa: BLE001
        record("db export", False, str(e))

    try:
        out = wp(
            "search-replace",
            "https://vertical-web.ddev.site",
            "https://example.invalid",
            "--all-tables",
            "--dry-run",
            "--format=count",
        )
        record("search-replace --dry-run", True, f"{out} rows would change")
    except Exception as e:  # noqa: BLE001
        record("search-replace --dry-run", False, str(e))

    try:
        record("option get", True, f"siteurl={wp('option', 'get', 'siteurl')}")
    except Exception as e:  # noqa: BLE001
        record("option get", False, str(e))

    try:
        n = wp("option", "list", "--format=count")
        record("option list (get all)", True, f"{n} options")
    except Exception as e:  # noqa: BLE001
        record("option list (get all)", False, str(e))

    try:
        record("eval (php exec)", True, f"PHP {wp('eval', 'echo PHP_VERSION;')}")
    except Exception as e:  # noqa: BLE001
        record("eval (php exec)", False, str(e))

    return checks


# --------------------------------------------------------------------------- #
# Section 2 — Module dependency catalog (#5)
# --------------------------------------------------------------------------- #
SHORTCODE_RE = re.compile(r"\[([a-z][a-z0-9_]+)")


def fetch_divi_content() -> list[dict]:
    """Return [{id, title, type, content}] for published pages + posts.

    Divi post_content is multi-line, so we cannot parse `wp db query` tab output
    row-by-row. Fetch the id/type/title list as JSON, then pull each post's
    content whole via `wp post get`.
    """
    listing = json.loads(
        wp(
            "post",
            "list",
            "--post_type=page,post",
            "--post_status=publish",
            "--fields=ID,post_type,post_title",
            "--format=json",
        )
    )
    items: list[dict] = []
    for row in listing:
        pid = str(row["ID"])
        content = wp("post", "get", pid, "--field=content")
        items.append(
            {
                "id": pid,
                "type": row.get("post_type", ""),
                "title": row.get("post_title") or "(untitled)",
                "content": content,
            }
        )
    return items


def module_catalog(items: list[dict]) -> dict:
    total = Counter()
    third_party_pages: dict[str, set[str]] = defaultdict(set)

    for it in items:
        tags = SHORTCODE_RE.findall(it["content"])
        for tag in tags:
            total[tag] += 1
            is_core = tag.startswith("et_pb_")
            if not is_core:
                label = f'{it["title"]} (#{it["id"]}, {it["type"]})'
                third_party_pages[tag].add(label)

    core = {t: c for t, c in total.items() if t.startswith("et_pb_") and t not in STRUCTURAL}
    structural = {t: c for t, c in total.items() if t in STRUCTURAL}
    third_party = {t: c for t, c in total.items() if not t.startswith("et_pb_")}

    return {
        "structural": dict(sorted(structural.items(), key=lambda kv: -kv[1])),
        "core_modules": dict(sorted(core.items(), key=lambda kv: -kv[1])),
        "third_party_modules": dict(sorted(third_party.items(), key=lambda kv: -kv[1])),
        "third_party_usage": {
            t: sorted(third_party_pages[t]) for t in sorted(third_party_pages)
        },
    }


# --------------------------------------------------------------------------- #
# Section 3 — Library / Theme Builder / Global Colors (#7)
# --------------------------------------------------------------------------- #
def list_posts(post_type: str) -> list[dict]:
    listing = json.loads(
        wp(
            "post",
            "list",
            f"--post_type={post_type}",
            "--post_status=publish,draft",
            "--fields=ID,post_title",
            "--format=json",
        )
    )
    return [
        {"id": str(row["ID"]), "title": row.get("post_title") or "(untitled)"}
        for row in listing
    ]


def global_colors_and_presets() -> dict:
    result: dict = {"global_colors": {}, "presets_present": False, "presets_bytes": 0}
    try:
        et_divi = json.loads(wp("option", "get", "et_divi", "--format=json"))
        if isinstance(et_divi, dict):
            # Divi 4 stores Global Colors under 'et_global_colors' (older builds
            # used 'global_colors'). Prefer the former, fall back to the latter.
            gc = et_divi.get("et_global_colors") or et_divi.get("global_colors")
            if gc:
                result["global_colors"] = gc
    except Exception:  # noqa: BLE001
        pass
    try:
        size = db(
            "SELECT LENGTH(option_value) FROM wp_options "
            "WHERE option_name='et_divi_builder_global_presets_ng';"
        ).strip()
        if size:
            result["presets_present"] = True
            result["presets_bytes"] = int(size)
    except Exception:  # noqa: BLE001
        pass
    return result


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def count(post_type: str) -> int:
    try:
        return int(wp("post", "list", f"--post_type={post_type}", "--format=count"))
    except Exception:  # noqa: BLE001
        return 0


def count_cmd(*args: str) -> int:
    try:
        return int(wp(*args, "--format=count"))
    except Exception:  # noqa: BLE001
        return 0


def build_report() -> dict:
    items = fetch_divi_content()
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "local DDEV replica (English) — https://vertical-web.ddev.site",
        "capability_checklist": capability_checklist(),
        "content_inventory": {
            "pages": count("page"),
            "posts": count("post"),
            "media": count("attachment"),
            "menus": count_cmd("menu", "list"),
            "active_plugins": count_cmd("plugin", "list", "--status=active"),
            "et_pb_layout_library": count("et_pb_layout"),
            "et_theme_builder": count("et_theme_builder"),
            "et_header_layout": count("et_header_layout"),
            "et_body_layout": count("et_body_layout"),
            "et_footer_layout": count("et_footer_layout"),
            "et_template": count("et_template"),
        },
        "module_catalog": module_catalog(items),
        "divi_library": list_posts("et_pb_layout"),
        "theme_builder": {
            "templates": list_posts("et_theme_builder"),
            "headers": list_posts("et_header_layout"),
            "bodies": list_posts("et_body_layout"),
            "footers": list_posts("et_footer_layout"),
        },
        "global_colors_presets": global_colors_and_presets(),
    }


def render_markdown(r: dict) -> str:
    ci = r["content_inventory"]
    mc = r["module_catalog"]
    gc = r["global_colors_presets"]

    lines: list[str] = []
    lines.append("# Divi module & asset catalog (English POC)")
    lines.append("")
    lines.append(
        "> Generated by `scripts/local/divi_recon.py` against the local DDEV replica. "
        "Re-run to refresh. Source of truth for issues #5, #7, #10."
    )
    lines.append(f">")
    lines.append(f"> Generated: {r['generated_utc']}")
    lines.append("")

    lines.append("## WP-CLI capability checklist (#10)")
    lines.append("")
    lines.append("| Capability | Status | Detail |")
    lines.append("|---|---|---|")
    for c in r["capability_checklist"]:
        lines.append(f"| {c['check']} | {'✅' if c['ok'] else '❌'} | {c['detail']} |")
    gaps = [c["check"] for c in r["capability_checklist"] if not c["ok"]]
    lines.append("")
    lines.append(f"**Gaps:** {'none — all verified' if not gaps else ', '.join(gaps)}")
    lines.append("")

    lines.append("## Content inventory (#7)")
    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|---|---|")
    for k, v in ci.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## Third-party module dependencies (#5)")
    lines.append("")
    if mc["third_party_modules"]:
        lines.append(
            "These non-core modules are used in real content and are **hard "
            "dependencies** — every environment (local, staging, Azure) must carry "
            "the add-on plugin that provides them or the layouts break."
        )
        lines.append("")
        lines.append("| Module shortcode | Uses | Provided by | Where |")
        lines.append("|---|---|---|---|")
        for tag, n in mc["third_party_modules"].items():
            provider = _provider_for(tag)
            where = "; ".join(mc["third_party_usage"].get(tag, [])) or "—"
            lines.append(f"| `{tag}` | {n} | {provider} | {where} |")
    else:
        lines.append("_No third-party modules detected in published content._")
    lines.append("")

    lines.append("## Core Divi modules in use (#5)")
    lines.append("")
    lines.append("| Module | Uses |")
    lines.append("|---|---|")
    for tag, n in mc["core_modules"].items():
        lines.append(f"| `{tag}` | {n} |")
    lines.append("")
    lines.append(
        "Structural containers: "
        + ", ".join(f"`{t}` ({n})" for t, n in mc["structural"].items())
    )
    lines.append("")

    lines.append("## Divi Library items (#7)")
    lines.append("")
    for p in r["divi_library"]:
        lines.append(f"- {p['title']} (#{p['id']})")
    lines.append("")

    lines.append("## Theme Builder (#7)")
    lines.append("")
    tb = r["theme_builder"]
    lines.append(f"- Templates: {len(tb['templates'])}")
    lines.append(f"- Header layouts: {len(tb['headers'])}")
    lines.append(f"- Body layouts: {len(tb['bodies'])}")
    lines.append(f"- Footer layouts: {len(tb['footers'])}")
    lines.append("")

    lines.append("## Global Colors & presets (#7)")
    lines.append("")
    n_colors = len(gc["global_colors"]) if gc["global_colors"] else 0
    lines.append(f"- Global Colors defined: {n_colors}")
    lines.append(
        f"- Global module presets (`et_divi_builder_global_presets_ng`): "
        f"{'present' if gc['presets_present'] else 'absent'} "
        f"({gc['presets_bytes']} bytes)"
    )
    lines.append("")
    return "\n".join(lines)


def _provider_for(tag: str) -> str:
    if tag.startswith("wdcl_"):
        return "WOW Divi Carousel Lite (`wow-carousel-for-divi-lite`)"
    if tag.startswith("dsm_"):
        return "Supreme Modules Lite (`supreme-modules-for-divi`)"
    return "unknown add-on"


def main() -> int:
    print("Running Divi recon against local DDEV replica ...")
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2))
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_markdown(report))
    print(f"  JSON:     {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"  Markdown: {OUT_MD.relative_to(REPO_ROOT)}")
    gaps = [c["check"] for c in report["capability_checklist"] if not c["ok"]]
    print(f"  Capability gaps: {'none' if not gaps else ', '.join(gaps)}")
    tp = report["module_catalog"]["third_party_modules"]
    print(f"  Third-party modules: {', '.join(tp) if tp else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
