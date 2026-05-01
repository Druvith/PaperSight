"""Shared patient field schema for PaperSight.

Single source of truth for the 8 extracted patient fields.
"""

from __future__ import annotations

from typing import TypedDict


class PatientField(TypedDict):
    key: str
    label: str


PATIENT_FIELDS: list[PatientField] = [
    {"key": "patient_name", "label": "Patient Name"},
    {"key": "age", "label": "Age"},
    {"key": "gender", "label": "Gender"},
    {"key": "chief_complaint", "label": "Chief Complaint"},
    {"key": "duration", "label": "Duration"},
    {"key": "allergies", "label": "Allergies"},
    {"key": "medications", "label": "Medications"},
    {"key": "referred_by", "label": "Referred By"},
]

# Keys only, handy for database column lists and dict construction.
PATIENT_KEYS = [f["key"] for f in PATIENT_FIELDS]
