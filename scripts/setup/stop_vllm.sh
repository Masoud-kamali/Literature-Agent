#!/bin/bash
# vLLM Server Stop Script

PORT="${VLLM_PORT:-8000}"

echo "Stopping vLLM server..."

# Find and kill processes
pkill -f "vllm.entrypoints.openai.api_server" && echo "✓ vLLM server stopped" || echo "No vLLM server running"

# Double check the port
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "Warning: Port $PORT is still in use"
    echo "Processes using port $PORT:"
    lsof -i :$PORT
else
    echo "✓ Port $PORT is free"
fi
