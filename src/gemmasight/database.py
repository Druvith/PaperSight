"""SQLite database layer for GemmaSight."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("gemmasight.db")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    age TEXT,
    gender TEXT,
    chief_complaint TEXT,
    duration TEXT,
    allergies TEXT,
    medications TEXT,
    referred_by TEXT,
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
    cursor = conn.execute(
        """
        INSERT INTO patients (
            patient_name, age, gender, chief_complaint, duration,
            allergies, medications, referred_by,
            priority, priority_label, wait_time, action,
            matched_rules, matched_descriptions, escalated, escalation_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            extracted.get("patient_name", ""),
            extracted.get("age", ""),
            extracted.get("gender", ""),
            extracted.get("chief_complaint", ""),
            extracted.get("duration", ""),
            extracted.get("allergies", ""),
            extracted.get("medications", ""),
            extracted.get("referred_by", ""),
            triage.get("priority", ""),
            triage.get("priority_label", ""),
            triage.get("wait_time", ""),
            triage.get("action", ""),
            ",".join(triage.get("matched_rules", [])),
            "; ".join(triage.get("matched_descriptions", [])),
            1 if triage.get("escalated") else 0,
            triage.get("escalation_reason", ""),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def list_patients(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM patients ORDER BY CASE priority WHEN 'red' THEN 1 WHEN 'yellow' THEN 2 WHEN 'green' THEN 3 ELSE 4 END, created_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def delete_patient(conn: sqlite3.Connection, patient_id: int) -> bool:
    cursor = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    return cursor.rowcount > 0
