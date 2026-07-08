"""FastAPI app — hybrid routing agent API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.metrics import STORE
from app.providers.fireworks_provider import ALLOWED_MODELS, FireworksProvider, MODEL_COSTS
from app.router import route
from app.schemas import BenchResult, MetricsSnapshot, Provider, RouteRequest, RouteResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("AMD Hybrid Router — Track 1")
    yield


app = FastAPI(title="AMD Hybrid Token-Efficient Router", version="0.1.0", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(Path(__file__).parent.joinpath("dashboard", "index.html").read_text())


@app.get("/playground", response_class=HTMLResponse)
async def playground() -> HTMLResponse:
    return HTMLResponse(Path(__file__).parent.joinpath("dashboard", "playground.html").read_text())


@app.post("/v1/route", response_model=RouteResponse)
async def api_route(req: RouteRequest) -> RouteResponse:
    try:
        return await route(req)
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.get("/v1/metrics", response_model=MetricsSnapshot)
async def api_metrics() -> dict:
    return STORE.snapshot()


@app.get("/v1/metrics/prometheus", response_class=PlainTextResponse)
async def api_metrics_prom() -> str:
    return STORE.prometheus_text()


@app.get("/v1/recent")
async def api_recent(limit: int = 10) -> list[dict]:
    return STORE.recent(limit=limit)


@app.get("/v1/health")
async def health() -> dict:
    statuses = {}
    async with httpx.AsyncClient(timeout=5) as c:
        for name, url in [("ollama", "http://localhost:11434"), ("ninerouter", "http://localhost:20128/")]:
            try:
                r = await c.get(url)
                statuses[name] = {"status": "up" if r.is_success else "degraded", "code": r.status_code}
            except httpx.RequestError:
                statuses[name] = {"status": "down"}
    statuses["fireworks"] = {"status": "configured" if bool(FireworksProvider().api_key) else "no_api_key"}
    return {"service": "hybrid-router", "version": "0.1.0", "providers": statuses}


@app.get("/v1/models")
async def api_models() -> list[dict]:
    return [
        {"id": m.split("/")[-1], "full_id": m,
         "cost_input_per_1k": MODEL_COSTS.get(m.split("/")[-1], (0, 0))[0],
         "cost_output_per_1k": MODEL_COSTS.get(m.split("/")[-1], (0, 0))[1]}
        for m in ALLOWED_MODELS
    ]
