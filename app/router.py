"""Router core — Fireworks model selector for Track 1 scoring."""

from __future__ import annotations

import logging

from app.metrics import STORE, RequestRecord
from app.providers.base import BaseProvider
from app.providers.fireworks_provider import FireworksProvider, ALLOWED_MODELS, MODEL_COSTS
from app.schemas import Complexity, Provider, RouteRequest, RouteResponse

log = logging.getLogger(__name__)

_COMPLEX_TRIGGERS = [
    "code", "debug", "refactor", "explain", "analyze", "compare",
    "write a", "create a", "generate a", "implement", "design a",
    "architecture", "algorithm", "optimize", "migrate",
]
_LONG_THRESHOLD = 500


def _estimate_complexity(prompt: str) -> Complexity:
    prompt_lower = prompt.lower()
    if any(trigger in prompt_lower for trigger in _COMPLEX_TRIGGERS):
        return Complexity.complex
    if len(prompt) > _LONG_THRESHOLD or len(prompt.split()) > 80:
        return Complexity.medium
    return Complexity.simple


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _find_model(match: str) -> str:
    for m in ALLOWED_MODELS:
        if match in m:
            return m
    return ALLOWED_MODELS[0]


# Model routing map: complexity → Fireworks model + cost reason
_MODEL_BY_COMPLEXITY = {
    Complexity.simple:    ("llama-v3p1-8b",     "$0.10/M tok input — cheapest, good for simple Q&A"),
    Complexity.medium:    ("qwen2p5-coder-7b",   "$0.20/M tok input — balanced speed/quality"),
    Complexity.complex:   ("qwen2p5-coder-32b",  "$0.80/M tok input — best quality for code/architecture"),
}

FALLBACK_MODEL = "llama-v3p1-8b"


def _select_fireworks_model(complexity: Complexity) -> tuple[str, str]:
    match, reason = _MODEL_BY_COMPLEXITY.get(
        complexity,
        _MODEL_BY_COMPLEXITY[Complexity.complex],
    )
    model_id = _find_model(match)
    return model_id, reason


_PROVIDER_INSTANCES: dict[Provider, BaseProvider] = {
    Provider.fireworks: FireworksProvider(),
}


async def route(req: RouteRequest) -> RouteResponse:
    complexity = _estimate_complexity(req.prompt)
    estimated_tokens = _estimate_tokens(req.prompt)

    primary_model, reason = _select_fireworks_model(complexity)
    fallback_models = [
        m for m in ALLOWED_MODELS
        if m != primary_model and "8b" in m or "7b" in m
    ]
    if not fallback_models or primary_model == FALLBACK_MODEL:
        fallback_models = [m for m in ALLOWED_MODELS if m != primary_model]

    provider = _PROVIDER_INSTANCES[Provider.fireworks]
    last_error: str | None = None
    result = None

    chain = [primary_model] + fallback_models[:2]  # try primary + 2 fallbacks
    for idx, model in enumerate(chain):
        log.info(
            "fireworks: %s (attempt %d/%d) — %s",
            model.split("/")[-1], idx + 1, len(chain), reason if idx == 0 else "fallback",
        )
        result = await provider.generate(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            model_override=model,
        )
        if result.success:
            break
        last_error = result.error
        log.warning("fireworks %s failed: %s", model, last_error)

    if result is None:
        raise RuntimeError("no fireworks model available")

    STORE.record(RequestRecord(
        provider=result.provider,
        model=result.model,
        tokens_input=result.tokens_input,
        tokens_output=result.tokens_output,
        latency_ms=result.latency_ms,
        cost_usd=result.cost_usd,
        success=result.success,
    ))

    return RouteResponse(
        result=result,
        complexity=complexity,
        estimated_tokens=estimated_tokens,
        fallback_chain=[Provider.fireworks, Provider.fireworks, Provider.fireworks],
        routed_to=Provider.fireworks,
    )