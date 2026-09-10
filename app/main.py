from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text
import httpx

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db, async_engine
from app.api.routes_interview import router as interview_router

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    yield
    await async_engine.dispose()


app = FastAPI(
    title="Vetta API",
    description="Automated Interview Assessment Platform: Multi-agent evaluation producing structured candidate scorecards.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router, prefix="/interviews", tags=["Interviews"])
app.include_router(interview_router, prefix="/api/v1/interviews", tags=["Interviews (v1)"])

STATIC_DIR = Path(__file__).parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Vetta API is running</h1><p><a href='/docs'>Swagger API Docs</a></p>")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_path = STATIC_DIR / "assets" / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path), media_type="image/x-icon")
    return HTMLResponse(content="", status_code=204)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "vetta-api",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health/ready", tags=["Health"])
async def health_ready():
    # Verify database connection
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    s3_status = "configured" if settings.is_s3_configured else "local_fallback"
    has_llm_key = bool(settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here")

    return {
        "status": "ready" if "unhealthy" not in db_status else "degraded",
        "database": db_status,
        "storage": s3_status,
        "llm_mode": "gemini" if has_llm_key else "heuristic_fallback",
        "api_key_configured": has_llm_key,
    }


@app.get("/health/llm", tags=["Health"])
async def health_llm():
    """Diagnostic check for LLM API key configuration and live model connectivity."""
    has_key = bool(settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here")
    if not has_key:
        return {
            "status": "heuristic_fallback",
            "api_key_configured": False,
            "message": "No Google/Gemini API key configured in environment. VETTA is operating with deterministic heuristic evaluation.",
            "model": settings.llm_model,
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.llm_model}:generateContent?key={settings.google_api_key}"
    payload = {"contents": [{"parts": [{"text": "Respond with the word OK if you receive this."}]}]}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                sample_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {
                    "status": "connected",
                    "api_key_configured": True,
                    "model": settings.llm_model,
                    "message": "Google Gemini API key is valid and operational.",
                    "sample_response": sample_text,
                }
            else:
                return {
                    "status": "error",
                    "api_key_configured": True,
                    "http_status": resp.status_code,
                    "message": f"Gemini API returned status {resp.status_code}",
                    "details": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                }
    except Exception as err:
        return {
            "status": "unreachable",
            "api_key_configured": True,
            "error": str(err),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)

