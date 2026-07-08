"""Router core — Fireworks model selector for Track 1 scoring."""

from __future__ import annotations

import logging

from app.metrics import STORE, RequestRecord
from app.providers.base import BaseProvider
from app.providers.fireworks_provider import FireworksProvider, ALLOWED_MODELS, MODEL_COSTS
from app.schemas import Complexity, Provider, RouteRequest, RouteResponse

log = logging.getLogger(__name__)

_COMPLEX_TRIGGERS = [
    "architecture", "design a", "implement a", "algorithm", "optimize", "migrate",
    "refactor", "debug this", "compare", "analyze",
]
_MEDIUM_TRIGGERS = [
    "write a", "create a", "generate a", "explain", "code", "function",
    "script", "method",
]
_LONG_THRESHOLD = 500


def _estimate_complexity(prompt: str) -> Complexity:
    prompt_lower = prompt.lower()
    if any(trigger in prompt_lower for trigger in _COMPLEX_TRIGGERS):
        return Complexity.complex
    if any(trigger in prompt_lower for trigger in _MEDIUM_TRIGGERS):
        return Complexity.medium
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
    Complexity.simple:    ("glm-5p1",           "$0.30/M tok — cheapest, good for simple Q&A"),
    Complexity.medium:    ("gpt-oss-120b",       "$0.50/M tok — balanced for code/explain"),
    Complexity.complex:   ("deepseek-v4-pro",   "$1.20/M tok — best reasoning for hard tasks"),
}

FALLBACK_MODEL = "glm-5p1"


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

    provider = _PROVIDER_INSTANCES[Provider.fireworks]
    result = await provider.generate(
        prompt=req.prompt,
        system_prompt=req.system_prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        model_override=primary_model,
    )
    if not result.success:
        log.warning("fireworks %s failed: %s — retrying with glm-5p1", primary_model.split("/")[-1], result.error)
        result = await provider.generate(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            model_override=ALLOWED_MODELS[0],
        )

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