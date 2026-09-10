import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "vetta-api"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "storage" in data


@pytest.mark.asyncio
async def test_llm_health_check(client: AsyncClient):
    response = await client.get("/health/llm")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "api_key_configured" in data


@pytest.mark.asyncio
async def test_rate_limiter_triggers_429(client: AsyncClient):
    from app.main import app, limiter
    from fastapi import Request

    @app.get("/test-rate-limit-check")
    @limiter.limit("2/minute")
    async def limited_endpoint(request: Request):
        return {"status": "ok"}

    r1 = await client.get("/test-rate-limit-check")
    assert r1.status_code == 200
    r2 = await client.get("/test-rate-limit-check")
    assert r2.status_code == 200
    r3 = await client.get("/test-rate-limit-check")
    assert r3.status_code == 429


