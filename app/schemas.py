"""Pydantic models for router requests/responses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Complexity(str, Enum):
    simple = "simple"
    medium = "medium"
    complex = "complex"


class Provider(str, Enum):
    ollama = "ollama"
    ninerouter = "ninerouter"
    fireworks = "fireworks"


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=128_000)
    system_prompt: str | None = None
    prefer_provider: Provider | None = None  # force a specific provider
    max_tokens: int = Field(default=4096, ge=1, le=128_000)
    temperature: float = Field(default=0.7, ge=0, le=2)


class ProviderResult(BaseModel):
    provider: Provider
    model: str
    output: str
    tokens_input: int
    tokens_output: int
    latency_ms: float  # end-to-end
    tpot_ms: float  # time-per-output-token
    cost_usd: float
    success: bool
    error: str | None = None


class RouteResponse(BaseModel):
    result: ProviderResult
    complexity: Complexity
    estimated_tokens: int
    fallback_chain: list[Provider]
    routed_to: Provider


class ProviderInfo(BaseModel):
    name: Provider
    models: list[str]
    status: str  # "available" | "unavailable"
    latency_p50_ms: float | None = None
    cost_per_1k_input: float
    cost_per_1k_output: float


class BenchResult(BaseModel):
    provider: Provider
    model: str
    prompt: str
    latency_ms: float
    tokens_per_sec: float
    success: bool
    error: str | None = None


class MetricsSnapshot(BaseModel):
    total_requests: int = 0
    success_rate: float = 1.0
    avg_latency_ms: float = 0
    avg_cost_usd: float = 0
    total_tokens: int = 0
    provider_breakdown: dict[str, Any] = {}
