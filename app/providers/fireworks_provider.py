"""Fireworks AI provider — Track 1 official scoring provider."""

from __future__ import annotations

import os
import time

import httpx

from app.providers.base import BaseProvider
from app.schemas import Provider, ProviderResult

FIREWORKS_BASE_URL = os.environ.get(
    "FIREWORKS_BASE_URL",
    "https://api.fireworks.ai/inference",
)
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")

ALLOWED_MODELS = [
    "accounts/fireworks/models/gpt-oss-120b",
    "accounts/fireworks/models/glm-5p1",
    "accounts/fireworks/models/glm-5p2",
    "accounts/fireworks/models/deepseek-v4-pro",
    "accounts/fireworks/models/kimi-k2p6",
    "accounts/fireworks/models/kimi-k2p5",
]

MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-oss-120b": (0.50, 0.80),       # mid-range, generic
    "glm-5p1": (0.30, 0.50),             # cheapest GLM
    "glm-5p2": (0.40, 0.60),             # slightly better GLM
    "deepseek-v4-pro": (1.20, 1.80),     # premium reasoning
    "kimi-k2p6": (0.60, 0.90),           # mid-high
    "kimi-k2p5": (0.80, 1.20),           # high quality
}


def _match_cost(model_id: str) -> tuple[float, float]:
    for key, costs in MODEL_COSTS.items():
        if key in model_id:
            return costs
    return (0.0, 0.0)


class FireworksProvider(BaseProvider):
    provider = Provider.fireworks
    default_model = "accounts/fireworks/models/glm-5p1"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or FIREWORKS_BASE_URL).rstrip("/")
        self.api_key = api_key or FIREWORKS_API_KEY

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model_override: str | None = None,
    ) -> ProviderResult:
        model = model_override or self.default_model
        url = f"{self.base_url}/v1/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=180) as c:
                resp = await c.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            elapsed = (time.monotonic() - start) * 1000
            status = e.response.status_code
            return ProviderResult(
                provider=self.provider,
                model=model,
                output="",
                tokens_input=0,
                tokens_output=0,
                latency_ms=round(elapsed, 1),
                tpot_ms=0,
                cost_usd=0,
                success=False,
                error=f"HTTP {status}: {e.response.text[:200]}",
            )
        except httpx.RequestError as e:
            elapsed = (time.monotonic() - start) * 1000
            return ProviderResult(
                provider=self.provider,
                model=model,
                output="",
                tokens_input=0,
                tokens_output=0,
                latency_ms=round(elapsed, 1),
                tpot_ms=0,
                cost_usd=0,
                success=False,
                error=str(e),
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        choice = data["choices"][0]
        output = choice["message"].get("content", "")
        usage = data.get("usage", {})
        tok_in = usage.get("prompt_tokens", 0)
        tok_out = usage.get("completion_tokens", 0)
        tpot = elapsed_ms / max(tok_out, 1)

        cost_input, cost_output = _match_cost(model)
        cost_in = (tok_in / 1_000_000) * cost_input
        cost_out = (tok_out / 1_000_000) * cost_output
        cost_usd = round(cost_in + cost_out, 10)

        return ProviderResult(
            provider=self.provider,
            model=model,
            output=output,
            tokens_input=tok_in,
            tokens_output=tok_out,
            latency_ms=round(elapsed_ms, 1),
            tpot_ms=round(tpot, 1),
            cost_usd=cost_usd,
            success=True,
        )

    def model_cost(self, model_id: str) -> tuple[float, float]:
        return _match_cost(model_id)