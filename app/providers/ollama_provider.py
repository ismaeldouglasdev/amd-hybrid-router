"""Ollama local provider."""

from __future__ import annotations

import time

import httpx

from app.providers.base import BaseProvider
from app.schemas import Provider, ProviderResult


class OllamaProvider(BaseProvider):
    """Runs Qwen 2.5 Coder / Gemma 4 locally via Ollama."""

    provider = Provider.ollama
    default_model = "qwen2.5-coder:1.5b"
    cost_per_1k_input = 0.0
    cost_per_1k_output = 0.0

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ProviderResult:
        url = f"{self.base_url}/api/generate"
        body = {
            "model": self.default_model,
            "prompt": prompt,
            "system": system_prompt or "",
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
            "stream": False,
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=120) as c:
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
        output = data.get("response", "")
        tok_in = data.get("prompt_eval_count", 0)
        tok_out = data.get("eval_count", 0)
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
