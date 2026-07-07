"""In-process metrics store with Prometheus-text export."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from app.schemas import Provider


@dataclass
class RequestRecord:
    provider: Provider
    model: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost_usd: float
    success: bool
    timestamp: float = field(default_factory=time.time)


class MetricsStore:
    """Thread-safe-ish metrics store (single-process, no locks needed for uvicorn single-worker)."""

    def __init__(self) -> None:
        self.records: list[RequestRecord] = []
        self._by_provider: dict[str, list[RequestRecord]] = defaultdict(list)

    def record(self, r: RequestRecord) -> None:
        self.records.append(r)
        self._by_provider[r.provider.value].append(r)

    def snapshot(self) -> dict:
        total = len(self.records)
        if total == 0:
            return {
                "total_requests": 0,
                "success_rate": 1.0,
                "avg_latency_ms": 0,
                "avg_cost_usd": 0,
                "total_tokens": 0,
                "provider_breakdown": {},
            }

        successes = sum(1 for r in self.records if r.success)
        avg_lat = sum(r.latency_ms for r in self.records) / total
        avg_cost = sum(r.cost_usd for r in self.records) / total
        total_tok = sum(r.tokens_input + r.tokens_output for r in self.records)

        breakdown = {}
        for prov, recs in self._by_provider.items():
            n = len(recs)
            breakdown[prov] = {
                "requests": n,
                "success_rate": sum(1 for r in recs if r.success) / n,
                "avg_latency_ms": sum(r.latency_ms for r in recs) / n,
                "avg_cost_usd": sum(r.cost_usd for r in recs) / n,
                "total_tokens": sum(r.tokens_input + r.tokens_output for r in recs),
            }

        return {
            "total_requests": total,
            "success_rate": successes / total,
            "avg_latency_ms": round(avg_lat, 1),
            "avg_cost_usd": round(avg_cost, 6),
            "total_tokens": total_tok,
            "provider_breakdown": breakdown,
        }

    def prometheus_text(self) -> str:
        snap = self.snapshot()
        lines = [
            '# HELP hybrid_router_requests_total Total requests routed',
            '# TYPE hybrid_router_requests_total counter',
            f'hybrid_router_requests_total {snap["total_requests"]}',
            '# HELP hybrid_router_success_rate Request success rate',
            '# TYPE hybrid_router_success_rate gauge',
            f'hybrid_router_success_rate {snap["success_rate"]}',
            '# HELP hybrid_router_avg_latency_ms Average latency',
            '# TYPE hybrid_router_avg_latency_ms gauge',
            f'hybrid_router_avg_latency_ms {snap["avg_latency_ms"]}',
            '# HELP hybrid_router_total_tokens Total tokens consumed',
            '# TYPE hybrid_router_total_tokens counter',
            f'hybrid_router_total_tokens {snap["total_tokens"]}',
        ]
        for prov, data in snap["provider_breakdown"].items():
            lines.append(f'hybrid_router_requests{{provider="{prov}"}} {data["requests"]}')
            lines.append(f'hybrid_router_latency_ms{{provider="{prov}"}} {data["avg_latency_ms"]}')
        return "\n".join(lines) + "\n"


STORE = MetricsStore()
