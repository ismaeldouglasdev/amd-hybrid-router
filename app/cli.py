#!/usr/bin/env python3
"""CLI — router run, bench, models, optimize."""

from __future__ import annotations

import asyncio
import time

import typer
from rich.console import Console
from rich.table import Table

from app.metrics import STORE
from app.router import route, _estimate_complexity, _select_fireworks_model
from app.schemas import RouteRequest
from app.providers.fireworks_provider import ALLOWED_MODELS, MODEL_COSTS, FireworksProvider

cli = typer.Typer(help="AMD Hybrid Token-Efficient Router — Track 1")
console = Console()


@cli.command()
def run(
    prompt: str,
    system: str | None = typer.Option(None, "--system", "-s", help="System prompt"),
    max_tokens: int = typer.Option(4096, "--max-tokens", "-m"),
    temperature: float = typer.Option(0.7, "--temp", "-t"),
    dry: bool = typer.Option(False, "--dry", help="Only show routing decision, no inference"),
) -> None:
    """Route a single prompt through the Fireworks model selector."""
    complexity = _estimate_complexity(prompt)
    model, reason = _select_fireworks_model(complexity)
    console.print(f"[bold]Complexity:[/] {complexity.value}")
    console.print(f"[bold]Selected model:[/] {model.split('/')[-1]}")
    console.print(f"[bold]Reason:[/] {reason}")

    if dry:
        return

    async def _run() -> None:
        req = RouteRequest(prompt=prompt, system_prompt=system, max_tokens=max_tokens, temperature=temperature)
        resp = await route(req)
        r = resp.result
        console.print(f"[bold]Latency:[/] {r.latency_ms}ms  |  TPOT: {r.tpot_ms}ms")
        console.print(f"[bold]Tokens:[/] {r.tokens_input} in / {r.tokens_output} out")
        console.print(f"[bold]Cost:[/] ${r.cost_usd:.6f}")
        if r.output:
            console.print(f"\n[bold]Output:[/]\n{r.output}")

    asyncio.run(_run())


@cli.command()
def models() -> None:
    """List available Fireworks models with costs."""
    table = Table(title="Fireworks AI Models — Track 1")
    table.add_column("Model ID", style="bold")
    table.add_column("Cost In/M tok")
    table.add_column("Cost Out/M tok")
    table.add_column("Best For")
    best_for = {
        "llama-v3p1-8b": "simple Q&A, factual",
        "qwen2p5-coder-7b": "mid complexity, code snippets",
        "qwen2p5-coder-32b": "complex code, architecture",
        "deepseek-v3p1": "heavy reasoning",
        "gemma-3-27b": "gemma bonus, balanced",
    }
    for m in ALLOWED_MODELS:
        short = m.split("/")[-1]
        ci, co = MODEL_COSTS.get(short, (0, 0))
        for key, desc in best_for.items():
            if key in m:
                table.add_row(short, f"${ci:.2f}", f"${co:.2f}", desc)
                break
        else:
            table.add_row(short, f"${ci:.2f}", f"${co:.2f}", "—")
    console.print(table)


@cli.command()
def optimize() -> None:
    """Analyze metrics and suggest routing rule adjustments."""
    snap = STORE.snapshot()
    if snap["total_requests"] == 0:
        console.print("[yellow]No data yet. Run some requests first.[/]")
        raise typer.Exit()

    console.print("[bold]Current Metrics[/]\n")
    for prov, data in snap["provider_breakdown"].items():
        console.print(f"  {prov}: {data['requests']} reqs, {data['avg_latency_ms']:.0f}ms avg, ${data['avg_cost_usd']:.6f}/req")

    suggestions = []
    fireworks = snap["provider_breakdown"].get("fireworks", {})
    if fireworks.get("requests", 0) < 10:
        suggestions.append("Need 10+ requests for meaningful optimization")

    console.print("\n[bold]Cost-Saving Suggestions[/]")
    for s in suggestions or ["Router online — everything $0 so far"]:
        console.print(f"  {s}")


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
