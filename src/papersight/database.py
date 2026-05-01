"""SQLite database layer for PaperSight."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .schema import PATIENT_KEYS

DB_PATH = Path("papersight.db")

# Patient columns come from schema; triage columns are appended.
_PATIENT_COLS = ", ".join(PATIENT_KEYS)
_TRIAGE_COLS = (
    "priority, priority_label, wait_time, action, "
    "matched_rules, matched_descriptions, escalated, escalation_reason"
)
_ALL_COLS = f"{_PATIENT_COLS}, {_TRIAGE_COLS}"

CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {_PATIENT_COLS.replace(", ", " TEXT,\n    ")} TEXT,
    priority TEXT,
    priority_label TEXT,
    wait_time TEXT,
    action TEXT,
    matched_rules TEXT,
    matched_descriptions TEXT,
    escalated INTEGER,
    escalation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_priority ON patients(priority);
CREATE INDEX IF NOT EXISTS idx_created ON patients(created_at);
"""


def init_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(CREATE_SQL)
    conn.commit()
    return conn


def insert_patient(conn: sqlite3.Connection, extracted: dict[str, Any], triage: dict[str, Any]) -> int:
    placeholders = ", ".join(["?"] * (len(PATIENT_KEYS) + 8))
    sql = f"""
        INSERT INTO patients (
            {_ALL_COLS}
        ) VALUES ({placeholders})
    """
    values = (
        *(extracted.get(k, "") for k in PATIENT_KEYS),
        triage.get("priority", ""),
        triage.get("priority_label", ""),
        triage.get("wait_time", ""),
        triage.get("action", ""),
        ",".join(triage.get("matched_rules", [])),
        "; ".join(triage.get("matched_descriptions", [])),
        1 if triage.get("escalated") else 0,
        triage.get("escalation_reason", ""),
    )
    cursor = conn.execute(sql, values)
    conn.commit()
    return cursor.lastrowid


_PRIORITY_ORDER = "CASE priority WHEN 'red' THEN 1 WHEN 'yellow' THEN 2 WHEN 'green' THEN 3 ELSE 4 END"


def list_patients(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"SELECT * FROM patients ORDER BY {_PRIORITY_ORDER}, created_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def delete_patient(conn: sqlite3.Connection, patient_id: int) -> bool:
    cursor = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    return cursor.rowcount > 0
