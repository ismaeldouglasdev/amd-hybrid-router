#!/usr/bin/env bash
# Quick-start for AMD Hackathon Hybrid Router
set -euo pipefail
cd "$(dirname "$0")"

# activate venv
source .venv/bin/activate

# start ollama if not running
if ! curl -sf http://localhost:11434 > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 2
fi

echo "=== AMD Hybrid Router ==="
echo "CLI:    router --help"
echo "API:    uvicorn app.main:app --reload --port 8000"
echo ""
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
