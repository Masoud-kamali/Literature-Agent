#!/bin/bash
# vLLM Server Startup Script for Literature Agent
# This script starts the vLLM server with proper authentication and logging

set -e  # Exit on error

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs/vllm"
LOG_FILE="${LOG_DIR}/vllm-server.log"
VLLM_ENV="${HOME}/miniforge-pypy3/envs/vllm"

# Model configuration
MODEL_NAME="${VLLM_MODEL:-meta-llama/Llama-3.1-8B-Instruct}"
HOST="${VLLM_HOST:-0.0.0.0}"
PORT="${VLLM_PORT:-8000}"
MAX_MODEL_LEN="${VLLM_MAX_LEN:-4096}"
GPU_MEMORY="${VLLM_GPU_MEM:-0.9}"

# Hugging Face token (required for gated models)
if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN environment variable not set."
    echo "For gated models like Llama, you need to set this:"
    echo "  export HF_TOKEN=your_token_here"
    echo ""
    read -p "Do you want to continue without authentication? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check if vLLM environment exists
if [ ! -d "$VLLM_ENV" ]; then
    echo "Error: vLLM environment not found at $VLLM_ENV"
    echo "Please run the installation script first."
    exit 1
fi

# Activate conda environment
echo "Activating vLLM environment..."
source "${HOME}/miniforge-pypy3/etc/profile.d/conda.sh"
conda activate vllm

# Check if server is already running
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "Error: Port $PORT is already in use"
    echo "Stop the existing vLLM server or use a different port"
    exit 1
fi

# Display configuration
echo "========================================"
echo "vLLM Server Configuration"
echo "========================================"
echo "Model: $MODEL_NAME"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Max Model Length: $MAX_MODEL_LEN"
echo "GPU Memory Utilization: $GPU_MEMORY"
echo "Log File: $LOG_FILE"
echo "========================================"
echo ""
echo "Starting vLLM server..."
echo "This will download the model on first run (~16GB for 8B model)"
echo ""

# Start vLLM server
nohup python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --dtype auto \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY" \
    > "$LOG_FILE" 2>&1 &

VLLM_PID=$!

echo "vLLM server started with PID: $VLLM_PID"
echo "Logs: tail -f $LOG_FILE"
echo ""
echo "Waiting for server to initialize..."

# Wait for server to be ready
sleep 5
for i in {1..60}; do
    if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
        echo "✓ Server is ready!"
        echo ""
        echo "Test the server:"
        echo "  curl http://localhost:$PORT/v1/models"
        echo ""
        echo "Stop the server:"
        echo "  kill $VLLM_PID"
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "Server did not become ready within 120 seconds."
echo "Check the logs: tail -f $LOG_FILE"
echo "The server may still be downloading the model."
exit 1
