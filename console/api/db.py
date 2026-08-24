"""
db.py — thin Postgres access layer for the console BFF (read-only for v0).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from config import settings


@contextmanager
def _conn():
    cfg = settings()["db"]
    conn = psycopg.connect(
        host=cfg["host"], port=cfg["port"], dbname=cfg["dbname"],
        user=cfg["user"], password=cfg["password"], connect_timeout=5,
    )
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with _conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def ping() -> bool:
    try:
        return query_one("SELECT 1 AS ok;") is not None
    except Exception:  # noqa: BLE001
        return False
