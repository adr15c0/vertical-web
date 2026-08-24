"""
config.py — console BFF configuration (env-driven).

Local dev defaults target the DDEV tooling DB (host port 5433) and the local
WordPress. Real credentials come from the environment / Key Vault, never Git.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load ONLY the console's own .env (do not walk up to the repo-root .env, whose
# TOOLING_DB_* placeholders would blank out our defaults).
load_dotenv(Path(__file__).resolve().parent / ".env")


@lru_cache
def settings() -> dict:
    return {
        "db": {
            "host": os.getenv("TOOLING_DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("TOOLING_DB_PORT", "5433")),
            "dbname": os.getenv("TOOLING_DB_NAME", "vertical_tooling"),
            "user": os.getenv("TOOLING_DB_USER", "tooling"),
            "password": os.getenv("TOOLING_DB_PASSWORD", "tooling"),
        },
        "wp": {
            "base_url": os.getenv("WP_BASE_URL", "https://vertical-web.ddev.site"),
            "user": os.getenv("WP_APP_USER", ""),
            "app_password": os.getenv("WP_APP_PASSWORD", ""),
            "verify_tls": os.getenv("WP_VERIFY_TLS", "false").lower() == "true",
        },
        # Comma-separated allowed origins for the React dev server.
        "cors_origins": os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(","),
    }
