"""Abstract provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import Provider, ProviderResult


class BaseProvider(ABC):
    """All providers implement this."""

    provider: Provider
    default_model: str
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ProviderResult: ...
