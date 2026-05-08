# PaperSight

Clinical triage assistant that photographs paper intake forms, extracts patient data with a vision LLM, and assigns priority scores using deterministic clinical rules — fully offline on a Mac Mini M2 with 8GB RAM.

Powered by **Gemma 4 E2B** via [Ollama](https://ollama.com) for on-device serving.

*Gemma is a trademark of Google LLC.*

Built for the **Kaggle "Gemma 4 Good Hackathon"** (deadline: May 18, 2026).

---

## What it does

1. **Photograph** a paper patient intake form with any smartphone, tablet, or desktop browser
2. **Extract** fields (name, age, gender, chief complaint, duration, allergies, medications, referred by) using Gemma 4 E2B via Ollama
3. **Triage** the patient with rule-based scoring derived from WHO ETAT + SATS + MSF guidelines
4. **Queue** patients by priority (Red → Yellow → Green) with filtering and detail views

**Only Age and Chief Complaint are required for triage.** All other fields are optional and collected at bedside if unreadable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Any Device)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Camera Input │  │ Triage Queue │  │ Patient Detail   │  │
│  │ (Drag/Drop)  │  │ (Filterable) │  │ Modal            │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │ HTTP
┌─────────▼───────────────────────────────────────────────────┐
│              FastAPI Server (Python, Offline)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  POST /api/extract                                  │   │
│  │    ├── Photo → Ollama (Gemma 4 E2B) → JSON extract  │   │
│  │    └── Extracted Data → Triage Engine → Priority    │   │
│  │  GET  /api/patients  ──→ SQLite (priority sorted)   │   │
│  │  DELETE /api/patients/{id} ──→ SQLite remove        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Ollama    │  │ TriageEngine │  │   SQLite     │     │
│  │ gemma4:e2b   │  │  27 Rules    │  │  patients.db │     │
│  │  (7.2 GB)    │  │ triage_rules │  │              │     │
│  │   Local      │  │   .json      │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Requirements

- macOS (tested on Mac Mini M2, 8GB RAM)
- [Ollama](https://ollama.com) v0.21.1+
- [uv](https://github.com/astral-sh/uv) for Python package management

---

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Pull the model (one-time, ~7.2GB)

```bash
ollama pull gemma4:e2b
```

### 3. Pre-warm Ollama (avoids ~57s cold-start)

```bash
ollama run gemma4:e2b "say ready"
```

### 4. Start the server

```bash
PYTHONPATH=src uv run uvicorn papersight.main:app --host 0.0.0.0 --port 8000
```

> **Note:** `PYTHONPATH=src` is currently required due to a module resolution issue with the `papersight-server` console script. Use `0.0.0.0` (not `127.0.0.1`) so other devices on the same Wi-Fi network can reach the server.

### 5. Open in browser

- **On this Mac:** `http://127.0.0.1:8000`
- **On phone / tablet (same Wi-Fi):** find your Mac's local IP with `ipconfig getifaddr en0`, then open `http://<YOUR_IP>:8000`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Serve frontend |
| `POST` | `/api/extract` | Upload photo → extract + triage |
| `GET`  | `/api/patients` | List all patients (priority sorted) |
| `DELETE` | `/api/patients/{id}` | Remove a patient |

---

## Key Design Decisions

- **Rule-based triage**, not LLM-based — deterministic, auditable, safe for clinical use
- **Static frontend modules** (`static/index.html`, `static/css/`, `static/js/`) — no build step, works offline, easy to iterate
- **Warm parchment theme** (`#ede8df`) — easier on eyes under fluorescent lighting
- **Temperature = 0** for deterministic JSON extraction
- **Hyphen normalization** (`chest-pain` → `chest pain`) before keyword matching
- **Elderly fall rule (R13)** — age > 60 + fall → automatic Red priority

---

## License

Apache 2.0
