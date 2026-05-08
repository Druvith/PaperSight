"""API tests for PaperSight endpoints.

Run with: uv run pytest tests/ -v
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

# Ensure src is on path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Use a test database
os.environ["PAPERSIGHT_DB"] = ":memory:"

from papersight.main import app
from papersight.database import init_db
from papersight.schema import PATIENT_KEYS

client = TestClient(app)

# Override the global db with in-memory for tests
import papersight.main as main_module
main_module.db = init_db(":memory:")


def _mock_ollama_response(chief_complaint: str = "Fever and chills"):
    """Return what _call_ollama would return after parsing: (extracted_dict, error_string)."""
    extracted = {k: "" for k in PATIENT_KEYS}
    extracted.update({
        "patient_name": "Maya Raman",
        "age": "43",
        "gender": "Female",
        "chief_complaint": chief_complaint,
        "duration": "3 days",
        "allergies": "Penicillin",
        "medications": "Metformin",
        "referred_by": "ASHA worker",
    })
    return extracted


def test_root_serves_index():
    """GET / should return the frontend HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_patients_empty():
    """GET /api/patients should return empty list initially."""
    response = client.get("/api/patients")
    assert response.status_code == 200
    data = response.json()
    assert "patients" in data
    assert data["patients"] == []


def test_extract_success():
    """POST /api/extract with a photo should return extracted data + triage."""
    photo_path = Path(__file__).parent / "fixtures" / "forms" / "form_01_clear.jpg"

    with patch.object(main_module, "_call_ollama", return_value=(_mock_ollama_response(), "")) as mock_ollama:
        with open(photo_path, "rb") as f:
            response = client.post("/api/extract", files={"photo": ("form_01_clear.jpg", f, "image/jpeg")})
        
        # Verify the mock was actually called
        assert mock_ollama.called, "Mock _call_ollama was not called - check patch target"

    assert response.status_code == 200
    data = response.json()

    assert "patient_id" in data
    assert "extracted" in data
    assert "triage" in data
    assert "timestamp" in data

    extracted = data["extracted"]
    assert extracted["patient_name"] == "Maya Raman"
    assert extracted["age"] == "43"

    triage = data["triage"]
    assert triage["priority"] == "yellow"
    assert triage["priority_label"] == "Priority"


def test_extract_ollama_offline():
    """POST /api/extract when Ollama is unreachable should return clear error."""
    photo_path = Path(__file__).parent / "fixtures" / "forms" / "form_01_clear.jpg"

    with patch.object(main_module, "_call_ollama", return_value=(None, "Cannot connect to Ollama")):
        with open(photo_path, "rb") as f:
            response = client.post("/api/extract", files={"photo": ("form_01_clear.jpg", f, "image/jpeg")})

    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "Extraction failed"
    assert "Ollama" in data["detail"]


def test_extract_chest_pain_triages_red():
    """Critical: chest pain should triage as red."""
    photo_path = Path(__file__).parent / "fixtures" / "forms" / "form_01_clear.jpg"

    with patch.object(main_module, "_call_ollama", return_value=(_mock_ollama_response("Chest pain"), "")):
        with open(photo_path, "rb") as f:
            response = client.post("/api/extract", files={"photo": ("form_01_clear.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert data["triage"]["priority"] == "red"


def test_extract_hyphenated_chest_pain():
    """Hyphenated 'chest-pain' should still triage as red after normalization."""
    photo_path = Path(__file__).parent / "fixtures" / "forms" / "form_01_clear.jpg"

    with patch.object(main_module, "_call_ollama", return_value=(_mock_ollama_response("chest-pain"), "")):
        with open(photo_path, "rb") as f:
            response = client.post("/api/extract", files={"photo": ("form_01_clear.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert data["triage"]["priority"] == "red"


def test_extract_persistence():
    """Extracted patient should appear in /api/patients list."""
    photo_path = Path(__file__).parent / "fixtures" / "forms" / "form_01_clear.jpg"

    # Extract a patient
    with patch.object(main_module, "_call_ollama", return_value=(_mock_ollama_response(), "")):
        with open(photo_path, "rb") as f:
            response = client.post("/api/extract", files={"photo": ("form_01_clear.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    patient_id = response.json()["patient_id"]

    # Verify in list
    response = client.get("/api/patients")
    assert response.status_code == 200
    patients = response.json()["patients"]
    ids = [p["id"] for p in patients]
    assert patient_id in ids


def test_extract_invalid_file():
    """POST without a photo file should fail gracefully."""
    response = client.post("/api/extract")
    assert response.status_code == 422  # FastAPI validation error
