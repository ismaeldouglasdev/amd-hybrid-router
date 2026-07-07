"""Router core — classifier + provider selector + fallback."""

from __future__ import annotations

import logging
import time

from app.metrics import STORE, RequestRecord
from app.providers.base import BaseProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.ninerouter_provider import NinerouterProvider
from app.schemas import Complexity, Provider, ProviderResult, RouteRequest, RouteResponse

log = logging.getLogger(__name__)

# Heuristics for complexity estimation (cheap, no extra LLM call)
_COMPLEX_TRIGGERS = [
    "code", "debug", "refactor", "explain", "analyze", "compare",
    "write a", "create a", "generate a", "implement", "design a",
    "architecture", "algorithm", "optimize", "migrate",
]
_LONG_THRESHOLD = 500  # chars


def _estimate_complexity(prompt: str) -> Complexity:
    prompt_lower = prompt.lower()
    word_count = len(prompt.split())
    char_count = len(prompt)

    if any(trigger in prompt_lower for trigger in _COMPLEX_TRIGGERS):
        return Complexity.complex
    if char_count > _LONG_THRESHOLD or word_count > 80:
        return Complexity.medium
    return Complexity.simple


def _estimate_tokens(text: str) -> int:
    """Very rough token estimate (~4 chars/token)."""
    return max(1, len(text) // 4)


# Decision thresholds
LOCAL_MAX_COMPLEXITY = Complexity.medium  # route simple/medium to local
LOCAL_MAX_TOKENS = 512  # skip local if estimated output tokens > this


def _select_provider(
    complexity: Complexity,
    estimated_tokens: int,
    prefer: Provider | None,
) -> tuple[Provider, list[Provider]]:
    """Return (primary, fallback_chain)."""
    if prefer:
        return prefer, [p for p in Provider if p != prefer]

    # simple/medium + short → local Ollama
    if complexity in (Complexity.simple, Complexity.medium) and estimated_tokens <= LOCAL_MAX_TOKENS:
        return Provider.ollama, [Provider.ninerouter]

    # everything else → remote 9router
    return Provider.ninerouter, [Provider.ollama]


_PROVIDER_INSTANCES: dict[Provider, BaseProvider] = {
    Provider.ollama: OllamaProvider(),
    Provider.ninerouter: NinerouterProvider(),
}


async def route(req: RouteRequest) -> RouteResponse:
    """Route a request through the hybrid decision engine."""
    complexity = _estimate_complexity(req.prompt)
    estimated_tokens = _estimate_tokens(req.prompt)
    primary, fallback_chain = _select_provider(complexity, estimated_tokens, req.prefer_provider)

    last_error: str | None = None
    result: ProviderResult | None = None

    # Try primary, then fallbacks
    chain = [primary] + fallback_chain
    for idx, prov in enumerate(chain):
        provider = _PROVIDER_INSTANCES[prov]
        log.info("routing to %s (attempt %d/%d)", prov.value, idx + 1, len(chain))
        result = await provider.generate(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        if result.success:
            break
        last_error = result.error
        log.warning("%s failed: %s — trying fallback", prov.value, last_error)

    if result is None:
        raise RuntimeError("no provider available")

    # Record metrics
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
        fallback_chain=fallback_chain,
        routed_to=result.provider,
    )
