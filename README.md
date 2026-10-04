# VETTA

Interview review workspace built with Python and FastAPI. Submit interview material, track assessment progress, and inspect structured technical and communication scorecards.

## Features

- Interview intake, artifact uploads, and a browser console.
- Separate technical review, communication assessment, and scorecard synthesis stages.
- Gemini integration with a heuristic fallback when a provider is unavailable.
- Async SQLAlchemy persistence with SQLite or PostgreSQL.
- Local artifact storage, optional S3 storage, and optional Celery processing.

## Run locally

Requires Python 3.11 or newer.

```bash
git clone https://github.com/Jemade/Vetta.git
cd Vetta
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 for the console or http://localhost:8000/docs for the API.

Defaults use SQLite and local storage. Use `.env.example` as the configuration reference; replace or remove placeholder credentials before loading it. Set `GOOGLE_API_KEY` and a supported `LLM_MODEL` for Gemini-backed assessment. Enable `USE_CELERY=true` and configure Redis when using Celery.

## Containers

```bash
docker compose up --build
```

Review the Compose environment and storage settings for your deployment.

## Tests

```bash
pip install pytest pytest-asyncio
pytest -q tests
```

## Code map

| Directory | Purpose |
| --- | --- |
| `app/agents/` | Review stages and pipeline |
| `app/api/` | Interview and health endpoints |
| `app/db/` | Persistence |
| `app/services/` | Artifact storage |
| `app/static/` | Web console |

## Current scope

Scorecards are review aids. Heuristic and model-generated scores are not validated hiring predictions. The default in-process task mode is intended for local development; durable distributed processing requires the Celery configuration.

## Engineering and contribution guide

Read the [engineering notes](docs/ENGINEERING.md) for implementation boundaries and verification commands, the [review checklist](docs/REVIEW_CHECKLIST.md) for evidence still required, and [CONTRIBUTING.md](CONTRIBUTING.md) to propose changes. Report vulnerabilities through [SECURITY.md](SECURITY.md).

[![Repository hygiene](https://github.com/Jemade/Vetta/actions/workflows/repository-hygiene.yml/badge.svg)](https://github.com/Jemade/Vetta/actions/workflows/repository-hygiene.yml)
