"""GemmaSight FastAPI server.

Endpoints:
  GET  /              — Serve frontend (responsive, works on any device)
  POST /api/extract   — Upload photo → extract JSON → triage → store → return
  GET  /api/patients  — List all processed patients (priority-sorted)
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db, insert_patient, list_patients, delete_patient
from .triage_engine import TriageEngine

# Directories
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="GemmaSight")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Database (single connection for demo; use pool in production)
db = init_db()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))

PROMPT = """You are a medical intake assistant at a rural hospital.
Extract the following from this photographed form and return ONLY valid JSON:
- patient_name
- age
- gender
- chief_complaint
- duration
- allergies
- medications
- referred_by

Copy the full text for each field exactly as written. Do not abbreviate or shorten.
If a field is completely unreadable due to scribbles or heavy blur, mark it "unreadable".
Do not add fields not listed above."""


def _strip_thinking(text: str) -> str:
    text = re.sub(r"<\|channel\|>thought\s*.*?<channel\|>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|think\|>.*?<\|/think\|>", "", text, flags=re.DOTALL)
    return text.strip()


def _call_ollama(image_bytes: bytes) -> tuple[dict[str, Any] | None, str]:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise data extraction assistant. Return ONLY valid JSON. No markdown, no commentary."},
            {"role": "user", "content": PROMPT, "images": [encoded]},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096, "top_p": 0.95, "top_k": 64},
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return None, f"Ollama returned HTTP {exc.code}: {error_body}"
    except urllib.error.URLError as exc:
        return None, f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running? ({exc})"
    except TimeoutError:
        return None, f"Ollama request timed out after {TIMEOUT}s. The model may still be loading into memory."
    except json.JSONDecodeError as exc:
        return None, f"Ollama returned non-JSON response: {exc}"

    text = str(body.get("message", {}).get("content", ""))
    text = _strip_thinking(text)

    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError:
        return None, f"Model did not return valid JSON. Raw output: {text[:500]}"

    if not isinstance(parsed, dict):
        return None, f"Model returned non-object JSON: {text[:500]}"

    return parsed, ""


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/extract")
def api_extract(photo: UploadFile = File(...)) -> JSONResponse:
    # 1. Save uploaded photo
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", photo.filename or "photo")
    upload_path = UPLOADS_DIR / f"{timestamp}_{safe_name}"
    image_bytes = photo.file.read()
    upload_path.write_bytes(image_bytes)

    # 2. Extract from photo via Ollama
    extracted, error = _call_ollama(image_bytes)
    if extracted is None:
        return JSONResponse(
            {"error": "Extraction failed", "detail": error},
            status_code=503,
        )

    # 3. Score triage
    engine = TriageEngine()
    triage = engine.evaluate(extracted)

    # 4. Persist
    patient_id = insert_patient(db, extracted, triage)

    # 5. Respond
    return JSONResponse({
        "patient_id": patient_id,
        "extracted": extracted,
        "triage": triage,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.get("/api/patients")
def api_patients() -> JSONResponse:
    return JSONResponse({"patients": list_patients(db)})


@app.delete("/api/patients/{patient_id}")
def api_delete_patient(patient_id: int) -> JSONResponse:
    deleted = delete_patient(db, patient_id)
    if not deleted:
        return JSONResponse({"error": "Patient not found"}, status_code=404)
    return JSONResponse({"deleted": True, "patient_id": patient_id})


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
