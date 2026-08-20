#!/usr/bin/env python3
"""
inventory_backup.py — Inventory + backup job for the English POC (issue #7).

Runs against the live DDEV replica and the local Postgres tooling DB. It:
  1. Builds a full Divi-aware inventory (reuses divi_recon.build_report):
     pages/posts/media/menus/plugins + Divi Library, Theme Builder, Global Colors.
  2. Produces a full backup artifact (a .tar.gz) containing:
       - database.sql            (wp db export)
       - inventory.json          (the recon report)
       - divi_library.json       (et_pb_layout posts, incl. content)
       - theme_builder.json      (theme builder templates + header/body/footer layouts)
       - global_colors.json      (et_global_colors from et_divi)
       - global_presets.json     (et_divi_builder_global_presets_ng)
       - manifest.json           (sha256 of every file + counts)
  3. Writes an inventory_snapshots row and job_log rows into the tooling DB.

Artifacts land under backups/en/artifacts/ (git-ignored).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_LOCAL = Path(__file__).resolve().parent
ARTIFACT_ROOT = REPO_ROOT / "backups" / "en" / "artifacts"
PG_CONTAINER = f"ddev-{REPO_ROOT.name}-postgres"
DB_NAME = "vertical_tooling"
DB_USER = "tooling"

sys.path.insert(0, str(SCRIPTS_LOCAL))
import divi_recon  # noqa: E402  (reuse the recon logic; import has no side effects)


def wp(*args: str) -> str:
    proc = subprocess.run(
        ["ddev", "wp", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ddev wp {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def psql(sql: str, variables: dict[str, str] | None = None) -> None:
    cmd = ["docker", "exec", "-i", PG_CONTAINER, "psql", "-v", "ON_ERROR_STOP=1"]
    for k, v in (variables or {}).items():
        cmd += ["-v", f"{k}={v}"]
    cmd += ["-U", DB_USER, "-d", DB_NAME]
    proc = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"psql failed: {proc.stderr.strip()}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2))


def log_job(status: str, context: dict, duration_ms: int | None = None,
            error: str | None = None) -> None:
    """Best-effort job_log write (never fails the backup)."""
    try:
        sql = (
            "INSERT INTO job_log(job, status, duration_ms, context, error) "
            "VALUES ('inventory_backup', :'st', "
            + ("NULL" if duration_ms is None else str(int(duration_ms)))
            + ", :'ctx'::jsonb, "
            + ("NULL" if error is None else ":'err'")
            + ");"
        )
        variables = {"st": status, "ctx": json.dumps(context)}
        if error is not None:
            variables["err"] = error[:4000]
        psql(sql, variables)
    except Exception as e:  # noqa: BLE001
        print(f"  (warning: job_log write failed: {e})", file=sys.stderr)


def main() -> int:
    started = time.time()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    work = ARTIFACT_ROOT / f"inventory-backup-{ts}"
    work.mkdir(parents=True, exist_ok=True)
    log_job("started", {"artifact_dir": str(work.relative_to(REPO_ROOT))})

    try:
        print(f"[1/6] Building Divi-aware inventory ...")
        report = divi_recon.build_report()
        write_json(work / "inventory.json", report)

        print("[2/6] Exporting database (wp db export) ...")
        (work / "database.sql").write_text(wp("db", "export", "-"))

        print("[3/6] Exporting Divi Library + Theme Builder ...")
        write_json(
            work / "divi_library.json",
            json.loads(wp("post", "list", "--post_type=et_pb_layout",
                          "--post_status=publish,draft",
                          "--fields=ID,post_title,post_content", "--format=json")),
        )
        tb = {}
        for pt in ("et_theme_builder", "et_header_layout",
                   "et_body_layout", "et_footer_layout"):
            tb[pt] = json.loads(wp("post", "list", f"--post_type={pt}",
                                   "--post_status=publish,draft",
                                   "--fields=ID,post_title,post_content",
                                   "--format=json"))
        write_json(work / "theme_builder.json", tb)

        print("[4/6] Exporting Global Colors + presets ...")
        et_divi = json.loads(wp("option", "get", "et_divi", "--format=json"))
        gc = {}
        if isinstance(et_divi, dict):
            gc = et_divi.get("et_global_colors") or et_divi.get("global_colors") or {}
        write_json(work / "global_colors.json", gc)
        try:
            presets = json.loads(
                wp("option", "get", "et_divi_builder_global_presets_ng", "--format=json")
            )
        except Exception:  # noqa: BLE001
            presets = {}
        write_json(work / "global_presets.json", presets)

        print("[5/6] Writing manifest + packaging artifact ...")
        files = sorted(p for p in work.iterdir() if p.is_file())
        manifest = {
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "site": "en",
            "environment": "local",
            "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                      for p in files},
            "counts": report["content_inventory"],
            "third_party_modules": report["module_catalog"]["third_party_modules"],
            "global_colors": len(gc) if hasattr(gc, "__len__") else 0,
        }
        write_json(work / "manifest.json", manifest)

        tarball = ARTIFACT_ROOT / f"inventory-backup-{ts}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(work, arcname=work.name)
        # Keep only the packaged artifact; drop the loose working directory.
        shutil.rmtree(work, ignore_errors=True)

        print("[6/6] Recording inventory_snapshots + job_log ...")
        summary = {
            "counts": report["content_inventory"],
            "third_party_modules": report["module_catalog"]["third_party_modules"],
            "divi_library": len(report["divi_library"]),
            "theme_builder": {k: len(v) for k, v in report["theme_builder"].items()},
            "global_colors": manifest["global_colors"],
            "capability_gaps": [c["check"] for c in report["capability_checklist"]
                                if not c["ok"]],
            "artifact_bytes": tarball.stat().st_size,
        }
        artifact_rel = str(tarball.relative_to(REPO_ROOT))
        psql(
            "INSERT INTO inventory_snapshots(environment, site, kind, summary, artifact_path) "
            "VALUES ('local', 'en', 'divi_recon', :'sum'::jsonb, :'ap');",
            {"sum": json.dumps(summary), "ap": artifact_rel},
        )

        duration_ms = int((time.time() - started) * 1000)
        log_job("success", {"artifact": artifact_rel,
                            "artifact_bytes": tarball.stat().st_size,
                            "counts": report["content_inventory"]}, duration_ms)

        print(f"\nDone in {duration_ms} ms")
        print(f"  Artifact: {artifact_rel} ({tarball.stat().st_size} bytes)")
        print(f"  Snapshot + job_log rows written to the tooling DB.")
        return 0

    except Exception as e:  # noqa: BLE001
        duration_ms = int((time.time() - started) * 1000)
        log_job("error", {"artifact_dir": str(work.relative_to(REPO_ROOT))},
                duration_ms, error=str(e))
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
