# PaperSight

<p align="center">
  <img src="assets/papersight_icon.png" width="120" alt="PaperSight logo">
</p>

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

![PaperSight Architecture](assets/architecture.png)

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

## Caveats & Limitations

PaperSight is **clinical decision-support**, not a replacement for trained clinical judgment. A nurse or doctor must always verify the triage and examine the patient.

- **Deterministic triage** — rule-based (WHO ETAT + SATS + MSF), not LLM-based. Auditable and reproducible, but cannot reason about novel or atypical presentations.
- **Brittle extraction** — vision model output depends on handwriting, blur, and lighting. Hyphenated compounds are normalized (`chest-pain` → `chest pain`), but there is no stemming or synonym expansion. Unreadable fields are marked `"unreadable"` and collected at bedside.
- **No vital signs** — triage is symptom-based only. BP, SpO₂, pulse, and temperature are not captured.
- **Offline constraints** — no cloud means no model updates, no sync, and no remote backup. The Mac Mini is a single point of failure.
- **Hardware ceiling** — 8GB RAM target. Image uploads capped at 10 MB. Context window limited to 4,096 tokens. No batch processing.

---

## License

Apache 2.0
