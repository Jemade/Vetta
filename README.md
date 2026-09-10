# VETTA — Autonomous Interview Assessment & Intelligence Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0_Async-red.svg)](https://docs.sqlalchemy.org/)
[![Render Live](https://img.shields.io/badge/Render-Deployed_Live-46E3B7.svg)](https://vetta-9xaz.onrender.com)
[![Docker Ready](https://img.shields.io/badge/Docker-Multi--stage-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live Production Web Console**: [https://vetta-9xaz.onrender.com](https://vetta-9xaz.onrender.com)  
**Live Swagger API Reference**: [https://vetta-9xaz.onrender.com/docs](https://vetta-9xaz.onrender.com/docs)

**VETTA** is an autonomous interview intelligence and assessment platform engineered for technical recruiters, engineering managers, and talent operations teams. It eliminates manual, subjective interview reviews by ingesting dialogue transcripts, technical artifacts, and audio recordings, evaluating candidates through an asynchronous dual-agent cognitive pipeline, and synthesizing rigorous, calibrated scorecards against enterprise benchmarks.

---

## 1. System Architecture

VETTA is architected as an event-driven, decoupled micro-monolith designed for horizontal scalability, sub-second API responsiveness, and zero-loss asynchronous processing.

```
                                  +---------------------------------------+
                                  |    Recruiter Web Console (SPA)        |
                                  | - Plus Jakarta Sans & JetBrains Mono  |
                                  | - 10s Startup Readiness Sequence      |
                                  | - Zero Fake Data / Dynamic Rendering  |
                                  +-------------------+-------------------+
                                                      |
                                     HTTP REST / JSON | (Multipart / Presigned URLs)
                                                      v
                                  +---------------------------------------+
                                  |        FastAPI Gateway Engine         |
                                  | - SlowAPI IP Rate Limiting            |
                                  | - Pydantic Strict Payload Validation  |
                                  | - Asynchronous DB Session Injection   |
                                  | - Liveness & Readiness Probes         |
                                  +---------+-------------------+---------+
                                            |                   |
                     +----------------------+                   +----------------------+
                     |                                                                 |
                     v                                                                 v
+---------------------------------------+                     +---------------------------------------+
|   SQLAlchemy 2.0 Async Persistence    |                     |      Storage Vault (Object Store)     |
| - SQLite (Zero-Config Local Dev)      |                     | - AWS S3 (Bucket Vaulting & Presign)  |
| - PostgreSQL (High-Concurrency Prod)  |                     | - Local Disk Fallback (storage_uploads)|
| - Strict Relationships & Cascade Del  |                     | - SHA-256 Checksum Validation         |
+---------------------------------------+                     +---------------------------------------+
                     ^                                                                 ^
                     |                                                                 |
                     +----------------------+                   +----------------------+
                                            |                   |
                                  +---------+-------------------+---------+
                                  |    Celery Worker Task Execution       |
                                  |    (Redis In-Memory Broker)           |
                                  | - Async Interview Task Queue          |
                                  | - Thread-safe In-Process Fallback     |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |      Dual-Agent Assessment Core       |
                                  |                                       |
                                  |  [Agent 1: Technical Reviewer]        |
                                  |  - Architecture & Systems Depth       |
                                  |  - Code Quality & Syntax Evaluation   |
                                  |  - Technical Gaps & Risk Detection    |
                                  |                                       |
                                  |  [Agent 2: Soft Skills Assessor]      |
                                  |  - Structure & Clarity Scoring        |
                                  |  - Conciseness & Articulation         |
                                  |  - Collaborative Mindset Calibration  |
                                  |                                       |
                                  |  [Synthesizer: Scorecard Engine]      |
                                  |  - 5-Axis Competency Radar Geometry   |
                                  |  - Executive Summary Formulation      |
                                  |  - 2nd-Round Probing Question Gen     |
                                  |                                       |
                                  |  * Google Gemini 1.5 Flash +          |
                                  |    Deterministic Heuristic Engine     |
                                  +---------------------------------------+
```

---

## 2. Core Capabilities & Autonomous Agents

### Autonomous Assessment Pipeline
* **Technical Reviewer Agent (`app/agents/technical_reviewer.py`)**: Analyzes conversation transcripts for distributed systems design, data structure selection, algorithmic tradeoffs, operational resilience, and architectural patterns. Discovers subtle knowledge gaps and generates actionable technical notes.
* **Soft Skills Assessor Agent (`app/agents/soft_skills_assessor.py`)**: Evaluates answer organization, clarity, structured communication (e.g., STAR method), active listening, conciseness, and cross-functional team alignment.
* **Scorecard Synthesizer (`app/agents/scorecard_synthesizer.py`)**: Integrates independent agent findings into a calibrated composite rating (0–10 scale), generates targeted follow-up probing questions, and maps candidate competency vectors across 5 dimensions against enterprise standards.
* **Resilient Multi-Tier AI Provider**: Supports Google Gemini 1.5 Flash for high-context neural synthesis, backed by a deterministic, offline-capable heuristic analyzer for air-gapped or offline environments.

### Recruiter Web Console
* **10-Second Startup Sequence**: Deliberate, cinematic boot sequence verifying backend readiness against `/health/ready` before gracefully revealing the workspace.
* **Zero Fake Data Architecture**: Virgin databases show clean, calibrated empty states with `0` metrics across all boards.
* **Role Benchmark Templates**: Quick configuration presets (*Lead Cloud Architect*, *Senior Fullstack Engineer*, *Associate Python Dev*) that populate intake inputs on demand without creating phantom records.
* **Candidate Dossier**: Complete dossier featuring overall scores, recommendation badges (*Strong Hire*, *Leaning Hire*, *Do Not Hire*), sub-dimension breakdown bars, 5-axis SVG radar polygon, identified gaps, customized follow-up questions, and audit remarks.
* **Audio Vault & Waveform Player**: Playback player with live audio timers, animated waveform equalizer, and automatic fallback when no recording is attached.
* **Master Directory & Search**: Real-time multi-field search (`⌘K` shortcut), status filtering, inspection, and record deletion.
* **Hiring Pipeline (Kanban)**: 4-stage progression (*New*, *Evaluating*, *Strong Hire*, *Review Needed*) calibrated to score cutoffs (&ge;7.5).
* **5-Axis Competency Radar**: Dynamic SVG radar polygon comparing candidate competence against the 7.5 enterprise baseline across Architecture, Coding, Communication, Problem Solving, and Ownership.
* **Analytics & Velocity**: Aggregate cohort statistics calculating mean technical depth, communication scores, and strong hire conversion ratios.
* **Real-time Audit Log**: Comprehensive timeline tracking assessment ingestion, S3 object vaulting, and multi-agent synthesis events.
* **Print Engine**: Dedicated `@media print` CSS generating clean, monochrome, boardroom-ready candidate scorecards.

---

## 3. Technology Stack Breakdown

| Layer | Technologies | Responsibility |
|---|---|---|
| **API Gateway** | FastAPI, Uvicorn, Starlette | High-throughput asynchronous REST routing, OpenAPI schema generation, dependency injection. |
| **Validation & Schema** | Pydantic v2, Pydantic-Settings | Strict request/response payload typing, environment configuration management. |
| **Persistence** | SQLAlchemy 2.0 (AsyncIO), SQLite, PostgreSQL, asyncpg, aiosqlite | Asynchronous ORM, transaction management, relationship loading (`selectinload`). |
| **Worker & Queue** | Celery, Redis | Distributed background task execution with automatic in-process fallback. |
| **Storage Vault** | AWS S3, Boto3, Local Storage Fallback | Immutable object storage, presigned upload URL generation, multi-format media ingestion. |
| **Cognitive Core** | Google Gemini 1.5 Flash, Deterministic Heuristics | Multi-agent interview evaluation, text processing, structured scorecard generation. |
| **Security & Limits** | SlowAPI (Limiter), CORS Middleware | Client rate limiting (60 req/min), CORS policy enforcement, sanitized diagnostics. |
| **Frontend Shell** | HTML5, Tailwind CSS, Plus Jakarta Sans, JetBrains Mono | Responsive, zero-dependency enterprise dark SaaS single-page application. |
| **Testing** | Pytest, Pytest-AsyncIO, HTTPX | Automated unit, integration, and end-to-end API lifecycle verification. |
| **Deployment** | Docker, Docker Compose, Kubernetes (K8s) | Containerized multi-service orchestration and production cloud manifests. |

---

## 4. Project Directory Structure

```
VETTA/
├── app/
│   ├── agents/                     # Multi-agent cognitive pipeline
│   │   ├── __init__.py
│   │   ├── base.py                 # Agent abstract base class & types
│   │   ├── technical_reviewer.py   # Technical reviewer agent
│   │   ├── soft_skills_assessor.py # Soft skills assessor agent
│   │   └── scorecard_synthesizer.py# Scorecard synthesizer & radar math
│   ├── api/                        # REST API routing layer
│   │   ├── __init__.py
│   │   ├── routes_health.py        # Liveness & readiness probes
│   │   └── routes_interview.py     # Intake, dossiers, audit log, uploads
│   ├── core/                       # Application configuration & logging
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic environment settings
│   │   └── logging.py              # Structured log formatting
│   ├── db/                         # Database models & async sessions
│   │   ├── __init__.py
│   │   ├── models.py               # Interview & Scorecard SQLAlchemy models
│   │   └── session.py              # Async engine & sessionmaker
│   ├── schemas/                    # Pydantic request & response schemas
│   │   ├── __init__.py
│   │   └── interview.py            # API request/response contracts
│   ├── services/                   # External service wrappers
│   │   ├── __init__.py
│   │   └── storage.py              # AWS S3 & local filesystem fallback
│   ├── static/                     # Persistent Web Console assets
│   │   ├── assets/
│   │   │   ├── favicon.svg         # Crisp geometric vector favicon
│   │   │   └── vetta_logo.jpg      # 3D VETTA emblem asset
│   │   └── index.html              # Enterprise SPA console (100% dynamic)
│   ├── tasks/                      # Distributed background workers
│   │   ├── __init__.py
│   │   └── worker.py               # Celery worker & evaluation task
│   └── main.py                     # FastAPI application factory & lifecycle
├── deploy/                         # Production deployment manifests
│   └── k8s/                        # Kubernetes Kustomize manifests
│       ├── api-deployment.yaml     # Replicated FastAPI pods with probes
│       ├── api-service.yaml        # ClusterIP routing
│       ├── configmap.yaml          # Non-sensitive configuration
│       ├── hpa.yaml                # Horizontal Pod Autoscaler (CPU/RAM)
│       ├── ingress.yaml            # Ingress controller with TLS
│       ├── kustomization.yaml      # Kustomize manifest bundle
│       ├── namespace.yaml          # Dedicated 'vetta' namespace
│       ├── secret.yaml             # Encrypted credentials & API keys
│       └── worker-deployment.yaml  # Celery background worker pods
├── storage_uploads/                # Local storage vault fallback directory
├── tests/                          # Automated Pytest test suite
│   ├── conftest.py                 # Async test client & database fixtures
│   ├── test_agents.py              # Multi-agent unit & synthesis tests
│   ├── test_health.py              # /health & /health/ready probe tests
│   ├── test_interviews_api.py      # End-to-end API lifecycle & audit tests
│   └── test_storage.py             # S3 mock & local storage tests
├── .env.example                    # Environment variable specification
├── Dockerfile                      # Multi-stage production container build
├── docker-compose.yml              # Complete 5-service local stack
├── pyproject.toml                  # Project packaging & dependencies
├── requirements.txt                # Pinned production requirements
└── README.md                       # Comprehensive platform documentation
```

---

## 5. Local Installation & Development Setup

### Prerequisites
* Python 3.11 or higher
* `pip` and virtual environment tool
* (Optional) Redis and Docker for distributed task processing

### Step-by-Step Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Jemade/Vetta.git
   cd Vetta
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` as appropriate. By default, VETTA works out-of-the-box using local SQLite (`vetta.db`), local disk storage (`storage_uploads/`), and in-process execution without external cloud dependencies.*

5. **Start the Development Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the Application**:
   * **Web Console**: `http://localhost:8000`
   * **Interactive OpenAPI Swagger Docs**: `http://localhost:8000/docs`
   * **Raw OpenAPI Specification**: `http://localhost:8000/openapi.json`
   * **Readiness Health Probe**: `http://localhost:8000/health/ready`

---

## 6. Docker & Containerized Deployment

Spin up the complete multi-service production stack (FastAPI gateway, Celery background worker, PostgreSQL 15, Redis 7, and LocalStack S3) with Docker Compose:

```bash
# Build images and start all services in the background
docker compose up -d --build

# Inspect running service status
docker compose ps

# View live service logs
docker compose logs -f api worker
```

### Exposed Endpoints in Docker Compose:
* **VETTA Web Console & API**: `http://localhost:8000`
* **PostgreSQL Database**: `localhost:5432` (`vetta` / `vetta_password`)
* **Redis In-Memory Broker**: `localhost:6379`
* **LocalStack S3 Service**: `http://localhost:4566`

To shut down and clean up containers and volumes:
```bash
docker compose down -v
```

---

## 7. Cloud Deployment on Render (render.com)

VETTA is deployed live in production on Render:
* **Production URL:** [https://vetta-9xaz.onrender.com](https://vetta-9xaz.onrender.com)
* **Detailed Deployment Guide:** See [DEPLOYMENT.md](DEPLOYMENT.md) for full cloud architecture, health probes, Docker configurations, and Kubernetes manifests.

### Option A: Render Blueprint (Infrastructure-as-Code)
1. Push your repository to GitHub or GitLab.
2. In the Render Dashboard, click **New +** -> **Blueprint**.
3. Select your VETTA repository. Render will automatically detect `render.yaml` and configure the Python web service.
4. Set the secret environment variable:
   * `GOOGLE_API_KEY`: Your Google Gemini API key.
5. Click **Apply**. Render will automatically build, test dependencies, and deploy the service with an auto-provisioned SSL certificate (`https://vetta-9xaz.onrender.com`).

### Option B: Manual Web Service Setup on Render
* **Runtime**: `Python`
* **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
* **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
* **Health Check Path**: `/health`
* **Environment Variables**:
  * `PYTHON_VERSION`: `3.11.9`
  * `ENVIRONMENT`: `production`
  * `GOOGLE_API_KEY`: `<your_gemini_api_key>`
  * `LLM_MODEL`: `gemini-3.6-flash`
  * `DATABASE_URL`: `sqlite+aiosqlite:///./vetta.db` *(or attach a free Render PostgreSQL database)*

---

## 8. Production Kubernetes Deployment

VETTA includes production-hardened Kubernetes manifests configured with non-root security contexts, resource requests/limits, liveness/readiness probes, horizontal auto-scaling, and TLS ingress routing:

```bash
# Preview manifests compiled by Kustomize
kubectl kustomize deploy/k8s/

# Apply all resources to your Kubernetes cluster
kubectl apply -k deploy/k8s/

# Verify pod readiness across the vetta namespace
kubectl get pods -n vetta -w
```

### Included Kubernetes Resources (`deploy/k8s/`):
* `namespace.yaml`: Isolated `vetta` namespace.
* `configmap.yaml`: Non-sensitive configuration (log levels, rate limits, bucket names).
* `secret.yaml`: Sealed secrets for database strings, AWS credentials, and Gemini API keys.
* `api-deployment.yaml`: Replicated API pods (2 replicas) with rolling update strategy, liveness probes (`/health`), and readiness probes (`/health/ready`).
* `worker-deployment.yaml`: Celery worker pods for asynchronous task processing.
* `api-service.yaml`: ClusterIP service distributing traffic across API pods on port 8000.
* `hpa.yaml`: Horizontal Pod Autoscaler dynamically scaling between 2 and 10 pods based on 70% CPU and 80% RAM utilization.
* `ingress.yaml`: NGINX Ingress resource with SSL/TLS termination.

---

## 9. Automated Testing Suite

VETTA maintains an automated test suite verifying agents, REST endpoints, storage engines, and readiness checks:

```bash
# Execute test suite with verbose output
pytest -v tests/

# Execute with code coverage report
pytest --cov=app --cov-report=term-missing tests/
```

### Test Coverage Breakdown:
* `tests/test_agents.py`: Technical reviewer heuristics, soft skills scoring, scorecard synthesis, canonical decision boundaries (5.49, 5.50, 7.49, 7.50, 10.0, 0.0), and 5-axis radar geometry calculations.
* `tests/test_health.py`: Liveness probe (`/health`), readiness probe (`/health/ready`), live LLM connectivity/diagnostic check (`/health/llm`), and SlowAPI rate limiter enforcement (HTTP 429).
* `tests/test_interviews_api.py`: Complete assessment creation, lifecycle polling, pagination, presigned uploads, direct multipart uploads, delete cascades, input validation rules, media streaming, path-traversal security, and audit log retrieval.
* `tests/test_storage.py`: Local disk storage lifecycle, file writing/reading, and Boto3 AWS S3 mocking.

---

## 10. REST API Reference

All responses adhere to strict JSON contracts. Unhandled exceptions return standardized RFC-7807 error envelopes.

| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/health` | Liveness probe returning operational state | None |
| `GET` | `/health/ready` | Readiness probe validating database & storage connectivity | None |
| `GET` | `/health/llm` | Diagnostic probe for LLM API key validation and model connectivity | None |
| `POST` | `/interviews/` | Ingest dialogue transcript & initiate multi-agent evaluation | 120 / min |
| `GET` | `/interviews/{id}` | Fetch candidate status, evaluation metrics, and scorecard | 120 / min |
| `GET` | `/interviews/` | List evaluated candidates (paginated: `page`, `size`) | 120 / min |
| `DELETE`| `/interviews/{id}` | Delete candidate assessment record and related scorecards | 120 / min |
| `GET` | `/interviews/audit-log` | Retrieve chronological system and agent audit events | 120 / min |
| `GET` | `/interviews/media/{key}` | Securely stream or download stored interview media artifacts | 120 / min |
| `POST` | `/interviews/presigned-upload` | Generate presigned AWS S3 upload URL for direct client vaulting | 120 / min |
| `POST` | `/interviews/upload-file` | Direct multipart file upload to storage vault (PDF, MP3, etc.) | 120 / min |

### Sample Intake Payload (`POST /interviews/`):
```json
{
  "candidate_name": "Marcus Vance",
  "candidate_email": "m.vance@enterprise.com",
  "role_title": "Lead Cloud Infrastructure Architect",
  "transcript": "Interviewer: How do you design multi-region Kubernetes architectures for resilience?\nCandidate: In our production setup, we deployed multi-cluster Kubernetes on AWS with cross-region replication. We used Terraform for declarative infrastructure as code, Cilium for eBPF-based service mesh and network security, and ArgoCD for GitOps pipelines. For storage, we leveraged S3 for immutable object storage and Aurora PostgreSQL with global databases...",
  "media_storage_key": "interviews/2026/09/session_rec_91a.mp3"
}
```

### Sample Response (`201 Created`):
```json
{
  "task_id": "c7a82b94-f18c-4f9e-8a2b-3e5f28c94012",
  "status": "PENDING"
}
```

---

## 11. Security, Storage Vault & Reliability

* **Rate Limiting**: Configured via SlowAPI at 60 requests per minute per IP to prevent denial-of-service and brute-force ingestion.
* **Storage Vault**: Supports AWS S3 with AES-256 server-side encryption and presigned tokens expiring after 900 seconds. If AWS credentials are not supplied, VETTA falls back to isolated local storage in `./storage_uploads/` without throwing unhandled exceptions.
* **Zero Secrets Exposure**: Startup failure diagnostics, error cards, and API error envelopes sanitize system internals and prevent leakage of database credentials, AWS secret keys, or environment secrets.
* **CORS Policy**: Configured in `app/main.py` to allow credentialed requests from authorized hiring portals.

---

## 12. Environment Configuration

| Variable | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `staging`, `production`) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./vetta.db` | Async SQLAlchemy database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URI for Celery background queue |
| `GOOGLE_API_KEY` | `""` | Google Gemini API key (defaults to deterministic heuristic if omitted) |
| `LLM_MODEL` | `gemini-3.6-flash` | Gemini model variant |
| `AWS_ACCESS_KEY_ID` | `""` | AWS S3 access key ID (defaults to local storage if omitted) |
| `AWS_SECRET_ACCESS_KEY` | `""` | AWS S3 secret access key |
| `AWS_REGION` | `us-east-1` | AWS S3 region |
| `AWS_S3_BUCKET` | `vetta-interview-vault` | Target AWS S3 bucket name |
| `RATE_LIMIT_PER_MINUTE` | `60` | SlowAPI rate limit threshold per client IP |

---

## 13. Troubleshooting & FAQ

**Q: What happens if `GEMINI_API_KEY` is not provided?**  
**A:** VETTA automatically engages its built-in deterministic heuristic evaluation engine. Assessments complete reliably with structured competency scores, gaps, and questions without failing or throwing external network errors.

**Q: How does the application handle cold starts during startup?**  
**A:** The recruiter web console runs a deliberate ~10-second boot sequence that queries `/health/ready` at second 7.0. If the service is still initializing, the user is presented with a calm diagnostic card with `[Retry Check]` and `[Proceed to Workspace]` actions.

**Q: Can I reset the database to a completely clean state?**  
**A:** Yes. Stop the server, delete `vetta.db`, and restart Uvicorn. The database will automatically initialize fresh tables with zero candidate records.

---

## License

VETTA is distributed under the terms of the [MIT License](LICENSE).
