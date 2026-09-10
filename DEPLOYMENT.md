# VETTA — Production Cloud & Infrastructure Deployment Guide

This document outlines the cloud deployment architecture, live production endpoints, container specifications, and operational verification procedures for **VETTA** (Autonomous Interview Assessment & Intelligence Platform).

---

## 1. Live Production Endpoints

| Resource | URL | Status | Description |
|---|---|---|---|
| **Recruiter Web Console** | [`https://vetta-9xaz.onrender.com`](https://vetta-9xaz.onrender.com/) | 🟢 **Live** | Interactive Single Page Application (SPA) dashboard |
| **Interactive API Docs** | [`https://vetta-9xaz.onrender.com/docs`](https://vetta-9xaz.onrender.com/docs) | 🟢 **Live** | OpenAPI / Swagger UI test suite |
| **ReDoc Specification** | [`https://vetta-9xaz.onrender.com/redoc`](https://vetta-9xaz.onrender.com/redoc) | 🟢 **Live** | Formal OpenAPI 3.1 documentation |
| **Liveness Probe** | [`https://vetta-9xaz.onrender.com/health`](https://vetta-9xaz.onrender.com/health) | 🟢 **Live** | Returns `{ "status": "ok", "service": "vetta-api" }` |
| **Readiness Probe** | [`https://vetta-9xaz.onrender.com/health/ready`](https://vetta-9xaz.onrender.com/health/ready) | 🟢 **Live** | Verifies database, storage vault, and LLM readiness |
| **LLM Health Probe** | [`https://vetta-9xaz.onrender.com/health/llm`](https://vetta-9xaz.onrender.com/health/llm) | 🟢 **Live** | Confirms active Google Gemini 3.6 Flash connectivity |
| **GitHub Repository** | [`https://github.com/Jemade/Vetta`](https://github.com/Jemade/Vetta) | 🟢 **Active** | Source repository with automated CI/CD integration |

---

## 2. Cloud Architecture (Render)

VETTA runs on **Render** as a high-performance web service built with Docker and managed through GitOps automation.

```
                  +-------------------------------------------------+
                  |              Cloudflare Edge (SSL)              |
                  |          https://vetta-9xaz.onrender.com        |
                  +------------------------+------------------------+
                                           |
                                           v
                  +-------------------------------------------------+
                  |               Render Web Service                |
                  | - Multi-Stage Python 3.12 Slim Container        |
                  | - Uvicorn ASGI Server with Dynamic $PORT Binding|
                  | - Non-root execution (`appuser:10001`)          |
                  | - Auto-Deploy on commit to `main`               |
                  +----+-----------------------+---------------+----+
                       |                       |               |
                       v                       v               v
            +---------------------+  +-------------------+  +---------------------+
            | SQLite DB Engine    |  | Storage Vault     |  | Google Gemini Core  |
            | (vetta.db)          |  | (Local Fallback/  |  | (gemini-3.6-flash)  |
            | Persistent Disk /   |  |  AWS S3 Bucket)   |  | Multi-Agent Engine  |
            | Async SQLAlchemy    |  |                   |  |                     |
            +---------------------+  +-------------------+  +---------------------+
```

### Render Configuration Details
* **Service Name:** `Vetta` (`srv-dahhapafngtc739nlil0`)
* **Environment:** `Docker` (or `Python 3.12`)
* **Region:** `Oregon (US West)`
* **Branch:** `main`
* **Auto-Deploy:** Enabled (new commits to `main` trigger zero-downtime rolling deploys)

### Production Environment Variables

| Variable | Configured Value | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Sets application runtime mode |
| `LOG_LEVEL` | `INFO` | Standard structured logging |
| `GOOGLE_API_KEY` | *(Encrypted Secret)* | Google Gemini generative AI authentication |
| `LLM_MODEL` | `gemini-3.6-flash` | Selected model variant for multi-agent synthesis |
| `DATABASE_URL` | `sqlite+aiosqlite:///./vetta.db` | Async SQLAlchemy SQLite database path |
| `RATE_LIMIT_PER_MINUTE` | `60` | SlowAPI client IP rate limiter threshold |

---

## 3. Infrastructure as Code: Blueprint (`render.yaml`)

To spin up a clone or staging instance with 1 click:
1. Connect your repository to Render.
2. Select **New +** -> **Blueprint**.
3. Render reads `render.yaml` automatically:

```yaml
services:
  - type: web
    name: vetta
    runtime: python
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    plan: free
    autoDeploy: true
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: PYTHON_VERSION
        value: "3.12"
      - key: LOG_LEVEL
        value: INFO
      - key: RATE_LIMIT_PER_MINUTE
        value: "60"
      - key: DATABASE_URL
        value: sqlite+aiosqlite:///./vetta.db
      - key: LLM_MODEL
        value: gemini-3.6-flash
      - key: GOOGLE_API_KEY
        sync: false
```

---

## 4. Container Deployment (Docker)

VETTA is packaged using a security-hardened, multi-stage `Dockerfile`:

```bash
# Build the production image locally
docker build -t vetta:latest .

# Run with local port mapping and environment variables
docker run -d \
  --name vetta-app \
  -p 8000:8000 \
  -e GOOGLE_API_KEY="your_api_key_here" \
  -e LLM_MODEL="gemini-3.6-flash" \
  vetta:latest

# Verify health status
curl http://localhost:8000/health
```

### Docker Hardening Features:
* **Builder Stage:** Compiles C dependencies (`build-essential`, `libpq-dev`) into wheels and discards compiler tools in the final image.
* **Non-Root User:** Runs strictly under unprivileged `appuser` (`UID: 10001`, `GID: 10001`).
* **Dynamic Cloud Ports:** Evaluates `PORT` dynamically via `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`.
* **Container Health Check:** Internal health probes query `http://localhost:${PORT:-8000}/health`.

---

## 5. Kubernetes Cluster Deployment (`deploy/k8s/`)

For enterprise Kubernetes deployments, manifests with horizontal autoscaling, non-root security contexts, and ingress routing are included in `deploy/k8s/`:

```bash
# Preview compiled Kustomize resources
kubectl kustomize deploy/k8s/

# Apply all resources to cluster
kubectl apply -k deploy/k8s/

# Verify running pods
kubectl get pods -n vetta -w
```

### Included Kubernetes Manifests:
* `namespace.yaml`: Isolated `vetta` namespace.
* `configmap.yaml` & `secret.yaml`: Cloud credentials and non-sensitive configs.
* `api-deployment.yaml`: Replicated API pods with rolling updates and readiness/liveness probes.
* `worker-deployment.yaml`: Celery asynchronous worker pods.
* `hpa.yaml`: Horizontal Pod Autoscaler scaling from 2 to 10 pods based on CPU/memory load.
* `ingress.yaml`: NGINX Ingress controller with TLS termination.

---

## 6. Live API Verification Commands

You can verify the live deployment directly from your terminal using `curl`:

```bash
# 1. Check system readiness
curl -s https://vetta-9xaz.onrender.com/health/ready

# 2. Check Google Gemini model connectivity
curl -s https://vetta-9xaz.onrender.com/health/llm

# 3. Create an interview evaluation
curl -s -X POST https://vetta-9xaz.onrender.com/interviews/ \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Marcus Vance",
    "candidate_email": "marcus.vance@enterprise.com",
    "role_title": "Lead Cloud Infrastructure Architect",
    "transcript": "Interviewer: How do you design resilient multi-region architectures on AWS?\nCandidate: In our architecture, we deploy Kubernetes clusters across three AWS regions with Route 53 latency-based routing and Aurora Global Databases for active-active cross-region read replication. S3 buckets use Cross-Region Replication with KMS encryption..."
  }'

# 4. Fetch evaluated scorecard by task ID
curl -s https://vetta-9xaz.onrender.com/interviews/<TASK_ID>
```
