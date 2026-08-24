#!/usr/bin/env python3
"""
validate_divi_json.py — CI check for issue #3.

Validates every Divi Library portability JSON under asset-pipeline/ against
asset-pipeline/schema/divi-library-layout.schema.json.

- Skips the schema file itself and any non-portability JSON (a file only fails if
  it *looks* like a Divi export — i.e. has a "context" or "data" key — but does
  not conform). Pure-data JSON with neither key is ignored.
- Exits 0 when nothing applicable is found (safe to run on every PR).

Usage: python3 scripts/ci/validate_divi_json.py [root ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed (pip install jsonschema)", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "asset-pipeline" / "schema" / "divi-library-layout.schema.json"


def looks_like_divi_export(obj: object) -> bool:
    return isinstance(obj, dict) and ("context" in obj or "data" in obj)


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] or [REPO_ROOT / "asset-pipeline"]
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)

    checked = 0
    failed = 0
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            if path.resolve() == SCHEMA_PATH.resolve() or "schema" in path.parts:
                continue
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError as e:
                print(f"::error file={path}::invalid JSON: {e}")
                failed += 1
                continue
            if not looks_like_divi_export(data):
                continue
            checked += 1
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                failed += 1
                for err in errors:
                    loc = "/".join(str(p) for p in err.path) or "(root)"
                    print(f"::error file={path}::{loc}: {err.message}")
            else:
                print(f"ok: {path.relative_to(REPO_ROOT)}")

    print(f"\nDivi JSON schema: {checked} export(s) checked, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
