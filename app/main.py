"""FastAPI app — hybrid routing agent API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from app.metrics import STORE
from app.router import route
from app.schemas import BenchResult, MetricsSnapshot, Provider, RouteRequest, RouteResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("AMD Hybrid Router — Track 1")
    yield


app = FastAPI(title="AMD Hybrid Token-Efficient Router", version="0.1.0", lifespan=lifespan)


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


@app.get("/v1/health")
async def health() -> dict:
    """Quick health check — pings Ollama and 9Router."""
    statuses = {}
    async with httpx.AsyncClient(timeout=5) as c:
        for name, url in [("ollama", "http://localhost:11434"), ("ninerouter", "http://localhost:8080/v1")]:
            try:
                r = await c.get(url)
                statuses[name] = {"status": "up" if r.is_success else "degraded", "code": r.status_code}
            except httpx.RequestError:
                statuses[name] = {"status": "down"}
    return {"service": "hybrid-router", "version": "0.1.0", "providers": statuses}


@app.post("/v1/bench", response_model=list[BenchResult])
async def api_bench(prompt: str = "Say hello in 5 words.") -> list[BenchResult]:
    """Benchmark all providers with a prompt."""
    results = []
    for prov in Provider:
        inst = {Provider.ollama: "app.providers.ollama_provider.OllamaProvider",
                Provider.ninerouter: "app.providers.ninerouter_provider.NinerouterProvider"}
        # lazy import
        import importlib
        mod_path, cls_name = inst[prov].rsplit(".", 1)
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        p = cls()
        res = await p.generate(prompt)
        results.append(BenchResult(
            provider=res.provider,
            model=res.model,
            prompt=prompt,
            latency_ms=res.latency_ms,
            tokens_per_sec=round(res.tokens_output / (res.latency_ms / 1000), 1) if res.latency_ms > 0 and res.tokens_output > 0 else 0,
            success=res.success,
            error=res.error,
        ))
    return results
