"""GemmaSight FastAPI server.

Endpoints:
  GET  /              — Serve frontend (responsive, works on any device)
  POST /api/extract   — Upload photo → extract JSON → triage → store → return
  GET  /api/patients  — List all processed patients (priority-sorted)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db, insert_patient, list_patients, delete_patient
from .schema import PATIENT_FIELDS
from .triage_engine import TriageEngine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gemmasight")


class RequestLoggingMiddleware:
    """ASGI middleware that logs every request with timing and status code."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 0)
                duration = (time.time() - start) * 1000
                logger.info("%s %s → %d (%.1f ms)", method, path, status, duration)
            await send(message)

        await self.app(scope, receive, wrapped_send)

# Directories resolved relative to this module (not CWD)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
STATIC_DIR = ROOT_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Image upload guard (prevent OOM on 8GB RAM target hardware)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Ollama configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))

# Database singleton — initialized on startup so tests can patch it.
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    db_path = os.environ.get("GEMMASIGHT_DB")
    db = init_db(db_path)
    logger.info("Database ready: %s", db_path or "gemmasight.db")
    logger.info("Ollama endpoint: %s | model: %s | timeout: %ds", OLLAMA_HOST, OLLAMA_MODEL, TIMEOUT)
    yield
    db.close()
    logger.info("Server shutting down — database closed.")


app = FastAPI(title="GemmaSight", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_FIELD_LIST = "\n".join(f"- {f['key']}" for f in PATIENT_FIELDS)
PROMPT = f"""You are a medical intake assistant at a rural hospital.
Extract the following from this photographed form and return ONLY valid JSON:
{_FIELD_LIST}

Copy the full text for each field exactly as written. Do not abbreviate or shorten.
If a field is completely unreadable due to scribbles or heavy blur, mark it "unreadable".
Do not add fields not listed above."""


# Pre-compiled patterns for stripping model "thinking" tags from output.
_THINKING_PATTERNS = [
    # Gemma-style channel thought blocks: <|channel|>thought ... <channel|>
    re.compile(r"<\|channel\|>thought\s*.*?<channel\|>", re.DOTALL),
    # Generic think tags: <|think|> ... <|/think|>
    re.compile(r"<\|think\|>.*?<\|/think\|>", re.DOTALL),
]


def _strip_thinking(text: str) -> str:
    for pat in _THINKING_PATTERNS:
        text = pat.sub("", text)
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
    logger.info("Ollama request → %s | image: %.1f KB", OLLAMA_MODEL, len(image_bytes) / 1024)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        logger.error("Ollama HTTP %d after %.1fs | %s", exc.code, time.time() - t0, error_body[:200])
        return None, f"Ollama returned HTTP {exc.code}: {error_body}"
    except urllib.error.URLError as exc:
        logger.error("Ollama unreachable after %.1fs | %s", time.time() - t0, exc)
        return None, f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running? ({exc})"
    except TimeoutError:
        logger.error("Ollama timeout after %ds", TIMEOUT)
        return None, f"Ollama request timed out after {TIMEOUT}s. The model may still be loading into memory."
    except json.JSONDecodeError as exc:
        logger.error("Ollama non-JSON response after %.1fs | %s", time.time() - t0, exc)
        return None, f"Ollama returned non-JSON response: {exc}"

    elapsed = time.time() - t0
    text = str(body.get("message", {}).get("content", ""))
    text = _strip_thinking(text)

    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError:
        logger.error("Model returned invalid JSON after %.1fs | raw: %s", elapsed, text[:300])
        return None, f"Model did not return valid JSON. Raw output: {text[:500]}"

    if not isinstance(parsed, dict):
        logger.error("Model returned non-object JSON after %.1fs | raw: %s", elapsed, text[:300])
        return None, f"Model returned non-object JSON: {text[:500]}"

    logger.info("Ollama OK ← %.1fs | fields: %s", elapsed, ", ".join(parsed.keys()))
    return parsed, ""


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/extract")
def api_extract(photo: UploadFile = File(...)) -> JSONResponse:
    # 1. Read and validate uploaded photo
    image_bytes = photo.file.read()
    filename = photo.filename or "photo"
    if len(image_bytes) > MAX_IMAGE_SIZE:
        logger.warning("Upload rejected: %s is %.1f MB (max %d MB)", filename, len(image_bytes) / (1024 * 1024), MAX_IMAGE_SIZE // (1024 * 1024))
        return JSONResponse(
            {"error": "File too large", "detail": f"Maximum image size is {MAX_IMAGE_SIZE // (1024 * 1024)} MB."},
            status_code=413,
        )

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    upload_path = UPLOADS_DIR / f"{timestamp}_{safe_name}"
    upload_path.write_bytes(image_bytes)
    logger.info("Upload saved: %s (%.1f KB)", upload_path.name, len(image_bytes) / 1024)

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
    logger.info(
        "Triage: %s → %s (%s) | rules: %s | escalated: %s",
        extracted.get("patient_name", "Unknown"),
        triage["priority"].upper(),
        triage["wait_time"],
        ", ".join(triage["matched_rules"]) or "none",
        "yes" if triage["escalated"] else "no",
    )

    # 4. Persist
    patient_id = insert_patient(db, extracted, triage)
    logger.info("Patient #%d persisted", patient_id)

    # 5. Respond
    return JSONResponse({
        "patient_id": patient_id,
        "extracted": extracted,
        "triage": triage,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.get("/api/patients")
def api_patients() -> JSONResponse:
    patients = list_patients(db)
    logger.info("Listed %d patient(s)", len(patients))
    return JSONResponse({"patients": patients})


@app.delete("/api/patients/{patient_id}")
def api_delete_patient(patient_id: int) -> JSONResponse:
    deleted = delete_patient(db, patient_id)
    if not deleted:
        logger.warning("Delete failed: patient #%d not found", patient_id)
        return JSONResponse({"error": "Patient not found"}, status_code=404)
    logger.info("Deleted patient #%d", patient_id)
    return JSONResponse({"deleted": True, "patient_id": patient_id})


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
