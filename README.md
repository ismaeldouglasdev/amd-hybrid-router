# AMD Hybrid Token-Efficient Routing Agent

**Track 1** — AMD Hackathon Act II

Hybrid router that decides local (Ollama) vs remote (9Router) inference based on task complexity, token budget, and latency.

## Quick Start

```bash
# deps
./start.sh

# CLI
router run "explain quantum computing in one sentence"
router bench
router optimize

# API
curl http://localhost:8000/v1/route -X POST -H 'Content-Type: application/json' \
  -d '{"prompt":"write hello world in python"}'
```

## Architecture

- `app/router.py` — classifier + provider selector + fallback chain
- `app/providers/ollama_provider.py` — local Ollama (Qwen 2.5 Coder 7B)
- `app/providers/ninerouter_provider.py` — remote 9Router (28-model combo)
- `app/metrics.py` — in-process metrics + Prometheus export
- `app/cli.py` — Typer CLI (run/bench/optimize/serve)

## Decision Logic

| Complexity | Est. Tokens | Route |
|-----------|------------|-------|
| simple | ≤512 | Ollama (local) |
| medium | ≤512 | Ollama (local) |
| complex/any | >512 | 9Router (remote) |

Fallback chain: primary → secondary on failure.
