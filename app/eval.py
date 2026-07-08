"""Accuracy eval for Track 1 scoring.

Tests router decisions against golden answers.
Outputs token count, cost, and accuracy metrics."""

from __future__ import annotations

import asyncio
import re
import statistics

from rich.console import Console
from rich.table import Table

from app.metrics import STORE
from app.router import route, _estimate_complexity, _select_fireworks_model
from app.schemas import RouteRequest
from app.providers.fireworks_provider import _match_cost

console = Console()

BENCHMARK = [
    {
        "task": "simple_qa",
        "prompt": "What is the capital of France?",
        "expected": ["Paris", "paris"],
        "min_tokens": 1,
    },
    {
        "task": "simple_qa",
        "prompt": "What is 2+2?",
        "expected": ["4", "four"],
        "min_tokens": 1,
    },
    {
        "task": "code_gen",
        "prompt": "Write a Python function that reverses a string.",
        "expected": ["def reverse", "return"],
        "min_tokens": 20,
        "code": True,
    },
    {
        "task": "code_gen",
        "prompt": "Write a function to check if a number is prime in Python.",
        "expected": ["def is_prime", "return", "if"],
        "min_tokens": 30,
        "code": True,
    },
    {
        "task": "code_debug",
        "prompt": "Fix this code: for i in range(10 print(i)",
        "expected": ["fix", ")"],
        "min_tokens": 10,
        "code": True,
    },
    {
        "task": "explain",
        "prompt": "Explain what an API is in one sentence.",
        "expected": ["application", "interface", "API"],
        "min_tokens": 10,
    },
    {
        "task": "explain",
        "prompt": "What is the difference between HTTP and HTTPS?",
        "expected": ["SSL", "TLS", "secure", "encrypt"],
        "min_tokens": 20,
    },
    {
        "task": "architecture",
        "prompt": "Compare REST and GraphQL. Which one would you use for a real-time chat app?",
        "expected": ["REST", "GraphQL", "real-time", "WebSocket"],
        "min_tokens": 50,
    },
]


def _check_accuracy(output: str, expected: list[str]) -> float:
    """Score 0-1 based on how many expected tokens appear in output."""
    output_lower = output.lower()
    matches = sum(1 for token in expected if token.lower() in output_lower)
    return matches / len(expected)


def _check_code(output: str) -> bool:
    """Check if output contains code blocks."""
    return bool(re.search(r"```|def |class |function |import ", output))


async def run_benchmark(limit: int | None = None) -> list[dict]:
    items = BENCHMARK[:limit] if limit else BENCHMARK
    results = []

    for item in items:
        prompt = item["prompt"]
        complexity = _estimate_complexity(prompt)
        model_id, reason = _select_fireworks_model(complexity)

        req = RouteRequest(prompt=prompt, max_tokens=512)
        resp = await route(req)
        r = resp.result

        accuracy = _check_accuracy(r.output, item["expected"])
        code_ok = _check_code(r.output) if item.get("code") else True

        results.append({
            "task": prompt[:40],
            "complexity": complexity.value,
            "model": r.model.split("/")[-1],
            "accuracy": accuracy,
            "code_ok": code_ok,
            "tokens": r.tokens_input + r.tokens_output,
            "cost": r.cost_usd,
            "latency_ms": r.latency_ms,
            "success": r.success,
            "expected": item["expected"],
            "output_preview": r.output[:80],
        })

    return results


def print_report(results: list[dict]) -> None:
    table = Table(title="Track 1 — Accuracy Benchmark")
    table.add_column("Task", style="bold")
    table.add_column("Model")
    table.add_column("Accuracy")
    table.add_column("Code?")
    table.add_column("Tokens")
    table.add_column("Cost")
    table.add_column("Latency")

    accuracies = []
    total_tokens = 0
    total_cost = 0.0
    pass_count = 0

    for r in results:
        acc = r["accuracy"]
        accuracies.append(acc)
        total_tokens += r["tokens"]
        total_cost += r["cost"]
        passed = acc >= 0.5 and (r["code_ok"] or not r.get("code_ok"))
        if passed:
            pass_count += 1

        color = "green" if passed else "red"
        table.add_row(
            f"[{color}]{'✓' if passed else '✗'}[/] {r['task']}",
            r["model"],
            f"{acc*100:.0f}%",
            "✓" if r["code_ok"] else "✗",
            str(r["tokens"]),
            f"${r['cost']:.6f}",
            f"{r['latency_ms']:.0f}ms",
        )

    console.print(table)

    avg_acc = statistics.mean(accuracies) if accuracies else 0
    print(f"\nResults:")
    print(f"  Pass rate:  {pass_count}/{len(results)} ({pass_count/len(results)*100:.0f}%)")
    print(f"  Avg accuracy: {avg_acc*100:.1f}%")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Total cost:   ${total_cost:.6f}")
    print(f"  Avg cost/req: ${total_cost/len(results):.6f}")
    print(f"  Avg latency:  {statistics.mean([r['latency_ms'] for r in results]):.0f}ms")
    print(f"\nProjection:")
    print(f"  1K reqs: ${total_cost/len(results)*1000:.4f}")
    print(f"  10K reqs: ${total_cost/len(results)*10000:.4f}")


if __name__ == "__main__":
    async def main():
        results = await run_benchmark()
        print_report(results)

    asyncio.run(main())