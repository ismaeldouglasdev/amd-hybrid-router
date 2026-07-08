# AMD Hybrid Token-Efficient Routing Agent

**Track 1** — AMD Hackathon Act II

[![AMD](https://img.shields.io/badge/AMD-Hackathon_Act_II-ED1C24)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

An intelligent routing agent that selects the cheapest Fireworks AI model that can still answer accurately — minimizing token usage without sacrificing output quality.

**Scored on:** Token count + output accuracy in the standardized Fireworks scoring environment.

---

## Quick Start

```bash
# 1. Set your Fireworks API key
export FIREWORKS_API_KEY="fw_3a_..."

# 2. Run via Docker
docker compose up

# 3. Route a prompt
curl http://localhost:8000/v1/route -X POST -H 'Content-Type: application/json' \
  -d '{"prompt":"write a python function to reverse a string"}'

# 4. Or use the CLI
pip install -e .
router run "explain quantum computing" --dry    # dry-run: see routing decision only
router models                                     # list available models + costs
```

---

## How It Works

```
Prompt → Complexity Classifier → Fireworks Model Selector → Inference
                │                        │
           simple → llama-8b      $0.10/M tok
           medium → qwen-7b       $0.20/M tok  
           complex → qwen-32b     $0.80/M tok
           gemma  → gemma-27b     $0.30/M tok (bonus pool eligible)
```

The router classifies each prompt by complexity (simple/medium/complex), then selects the cheapest Fireworks model that meets the accuracy threshold. If the primary model fails, it falls back to the next cheapest.

### Decision Table

| Prompt Type | Example | Model | Cost/M tok input |
|------------|---------|-------|-----------------|
| Simple Q&A | "What is the capital of France?" | `llama-v3p1-8b` | $0.10 |
| Code snippet | "Write a function to reverse a string" | `qwen2p5-coder-7b` | $0.20 |
| Complex code | "Implement a balanced BST" | `qwen2p5-coder-32b` | $0.80 |
| Reasoning | "Compare REST vs GraphQL" | `deepseek-v3p1` | $1.20 |
| Bonus | Any prompt (Gemma prize) | `gemma-3-27b` | $0.30 |

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard (HTML) |
| `/v1/route` | POST | Route a prompt through the model selector |
| `/v1/models` | GET | List available models + costs |
| `/v1/metrics` | GET | Metrics snapshot (JSON) |
| `/v1/metrics/prometheus` | GET | Prometheus-format metrics |
| `/v1/recent` | GET | Recent request log |
| `/v1/health` | GET | Health check |

### POST `/v1/route`

```json
{
  "prompt": "write a python function to reverse a string",
  "system_prompt": "You are a helpful coding assistant.",
  "max_tokens": 4096,
  "temperature": 0.7
}
```

### Response

```json
{
  "result": {
    "provider": "fireworks",
    "model": "accounts/fireworks/models/qwen2p5-coder-7b-instruct",
    "output": "def reverse_string(s):\n    return s[::-1]",
    "tokens_input": 45,
    "tokens_output": 28,
    "latency_ms": 1234.5,
    "cost_usd": 0.000012,
    "success": true
  },
  "complexity": "medium",
  "estimated_tokens": 12,
  "routed_to": "fireworks"
}
```

---

## CLI

```bash
# Install
pip install -e .

# Commands
router run "prompt"           # Route + inference
router run "prompt" --dry     # Show routing decision only
router models                  # List models + costs
router optimize                # Analyze metrics, suggest improvements
router serve                   # Start API server
```

---

## Accuracy Eval

```bash
python -m app.eval
```

Runs the router against a benchmark of 8 tasks (Q&A, code gen, debug, explain, architecture), measures accuracy per task, and projects costs at scale.

---

## Containerization

```bash
# Standard image
docker build -t amd-hybrid-router .
docker run -e FIREWORKS_API_KEY=$FIREWORKS_API_KEY -p 8000:8000 amd-hybrid-router

# Scoring environment (minimal, no local models)
docker build -f Dockerfile.scoring -t amd-hybrid-router-scoring .
docker run -e FIREWORKS_API_KEY=$FIREWORKS_API_KEY -p 8000:8000 amd-hybrid-router-scoring

# Or with compose
FIREWORKS_API_KEY=fw_3a_... docker compose up
```

---

## Architecture

```
app/
├── main.py              # FastAPI server + routes
├── router.py            # Complexity classifier + model selector + fallback
├── eval.py              # Accuracy benchmark (Track 1 scoring)
├── metrics.py           # In-memory metrics store + Prometheus export
├── schemas.py           # Pydantic models
├── cli.py               # Typer CLI
├── providers/
│   ├── fireworks_provider.py  # Fireworks AI (scoring provider)
│   ├── ollama_provider.py     # Ollama local (dev only)
│   └── ninerouter_provider.py # 9Router (dev only)
└── dashboard/
    └── index.html       # Real-time metrics dashboard
```

---

## Cost Projection

| Volume | Mix | Daily Cost | Monthly Cost |
|--------|-----|-----------|-------------|
| 1K reqs | 70% llama-8b + 30% qwen-7b | $0.13 | $3.90 |
| 10K reqs | mixed | $1.30 | $39.00 |
| 100K reqs | mixed | $13.00 | $390.00 |

With the $50 Fireworks credits from the AMD AI Developer Program, moderate usage is free for ~4 months.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FIREWORKS_API_KEY` | ✅ | — | Fireworks AI API key |
| `FIREWORKS_BASE_URL` | ❌ | `https://api.fireworks.ai/inference/v1` | API base URL |

---

## Resources

- [AMD Hackathon Act II](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii)
- [Fireworks AI Docs](https://docs.fireworks.ai/)
- [AMD AI Developer Program](https://www.amd.com/en/developer/ai-dev-program.html)
