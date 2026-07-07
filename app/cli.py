#!/usr/bin/env python3
"""CLI — router run, bench, optimize."""

from __future__ import annotations

import asyncio
import json
import time

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from app.metrics import STORE
from app.router import route
from app.schemas import RouteRequest

cli = typer.Typer(help="AMD Hybrid Token-Efficient Router")
console = Console()


@cli.command()
def run(
    prompt: str,
    system: str | None = typer.Option(None, "--system", "-s", help="System prompt"),
    max_tokens: int = typer.Option(4096, "--max-tokens", "-m"),
    temperature: float = typer.Option(0.7, "--temp", "-t"),
) -> None:
    """Route a single prompt through the hybrid engine."""
    async def _run() -> None:
        req = RouteRequest(prompt=prompt, system_prompt=system, max_tokens=max_tokens, temperature=temperature)
        resp = await route(req)
        r = resp.result
        console.print(f"[bold]Routed to:[/] {r.provider.value} / {r.model}")
        console.print(f"[bold]Complexity:[/] {resp.complexity.value}")
        console.print(f"[bold]Latency:[/] {r.latency_ms}ms  |  TPOT: {r.tpot_ms}ms")
        console.print(f"[bold]Tokens:[/] {r.tokens_input} in / {r.tokens_output} out")
        console.print(f"[bold]Cost:[/] ${r.cost_usd:.6f}")
        if r.output:
            console.print(f"\n[bold]Output:[/]\n{r.output}")

    asyncio.run(_run())


@cli.command()
def bench(
    prompt: str = "Write a short poem about AI routing.",
    count: int = typer.Option(3, "--count", "-c", help="Runs per provider"),
) -> None:
    """Benchmark all providers and compare."""
    async def _bench() -> None:
        from app.providers.ollama_provider import OllamaProvider
        from app.providers.ninerouter_provider import NinerouterProvider

        providers = {"ollama": OllamaProvider(), "9router": NinerouterProvider()}
        table = Table(title=f"Benchmark: {count} runs each")
        table.add_column("Provider", style="bold")
        table.add_column("Model")
        table.add_column("Success", justify="right")
        table.add_column("Avg Latency", justify="right")
        table.add_column("Tokens/s", justify="right")

        for name, prov in providers.items():
            latencies = []
            tok_rates = []
            ok = 0
            for i in range(count):
                res = await prov.generate(prompt)
                if res.success:
                    ok += 1
                    latencies.append(res.latency_ms)
                    tok_rates.append(res.tokens_output / (res.latency_ms / 1000) if res.latency_ms > 0 else 0)
            avg_lat = sum(latencies) / len(latencies) if latencies else 0
            avg_tok = sum(tok_rates) / len(tok_rates) if tok_rates else 0
            s = f"{ok}/{count}"
            table.add_row(name, prov.default_model, s, f"{avg_lat:.0f}ms", f"{avg_tok:.1f}")

        console.print(table)

    asyncio.run(_bench())


@cli.command()
def optimize() -> None:
    """Analyze metrics and suggest routing rule adjustments."""
    snap = STORE.snapshot()
    if snap["total_requests"] == 0:
        console.print("[yellow]No data yet. Run some requests first.[/]")
        raise typer.Exit()

    console.print("[bold]Optimization Suggestions[/]\n")
    for prov, data in snap["provider_breakdown"].items():
        console.print(f"{prov}: {data['requests']} reqs, {data['avg_latency_ms']:.0f}ms avg, ${data['avg_cost_usd']:.6f}/req")

    # Heuristic: if local is fast enough (p50 < 2s), prefer local for more tasks
    local = snap["provider_breakdown"].get("ollama")
    remote = snap["provider_breakdown"].get("ninerouter")
    suggestions = []
    if local and remote:
        if local["avg_latency_ms"] < 2000 and local["avg_latency_ms"] < remote["avg_latency_ms"] * 1.5:
            suggestions.append("→ Local Ollama is competitive. Consider raising LOCAL_MAX_TOKENS in router.py.")
        if remote["success_rate"] < 0.8:
            suggestions.append("→ 9Router success rate low. Check NINEROUTER_URL or model availability.")
    if not suggestions:
        suggestions.append("→ Need more data. Run 10+ requests across both providers.")

    for s in suggestions:
        console.print(s)


@cli.command()
def dashboard() -> None:
    """Open web dashboard URL."""
    console.print("[green]Dashboard:[/] http://localhost:8000/v1/metrics")
    console.print("[green]Prometheus:[/] http://localhost:8000/v1/metrics/prometheus")


@cli.command()
def serve(port: int = typer.Option(8000, "--port", "-p", help="FastAPI port")) -> None:
    """Start the API server."""
    import uvicorn
    console.print(f"[green]Starting server on :{port}[/]")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    cli()
