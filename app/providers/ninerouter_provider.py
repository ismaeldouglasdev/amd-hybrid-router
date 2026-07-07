"""9Router remote provider — OpenAI-compatible gateway."""

from __future__ import annotations

import json
import os
import time

import httpx

from app.providers.base import BaseProvider
from app.schemas import Provider, ProviderResult

NINEROUTER_URL = os.environ.get("NINEROUTER_URL", "http://localhost:8080/v1")


class NinerouterProvider(BaseProvider):
    """Routes through 9Router's round-robin combo for $0 inference."""

    provider = Provider.ninerouter
    default_model = "combo-a"  # 28-model round-robin — free
    cost_per_1k_input = 0.0
    cost_per_1k_output = 0.0

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or NINEROUTER_URL).rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ProviderResult:
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=180) as c:
                resp = await c.post(url, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.RequestError as e:
            elapsed = (time.monotonic() - start) * 1000
            return ProviderResult(
                provider=self.provider,
                model=self.default_model,
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
        output = choice["message"]["content"]
        usage = data.get("usage", {})
        tok_in = usage.get("prompt_tokens", 0)
        tok_out = usage.get("completion_tokens", 0)
        tpot = elapsed_ms / max(tok_out, 1)

        return ProviderResult(
            provider=self.provider,
            model=self.default_model,
            output=output,
            tokens_input=tok_in,
            tokens_output=tok_out,
            latency_ms=round(elapsed_ms, 1),
            tpot_ms=round(tpot, 1),
            cost_usd=0.0,
            success=True,
        )
