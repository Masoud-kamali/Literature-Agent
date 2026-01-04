# Makefile for literature agent

.PHONY: install test run clean lint format help

help:
	@echo "Literature Agent - Available Commands"
	@echo "====================================="
	@echo "install       - Install dependencies with Poetry"
	@echo "test          - Run test suite"
	@echo "test-cov      - Run tests with coverage report"
	@echo "run           - Run weekly agent (default: 7 days)"
	@echo "backfill      - Run backfill for 30 days"
	@echo "lint          - Run ruff linter"
	@echo "format        - Format code with black"
	@echo "clean         - Remove generated files"
	@echo "vllm-start    - Print vLLM start command"

install:
	poetry install

test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term

run:
	poetry run python scripts/run_weekly.py

backfill:
	poetry run python scripts/backfill.py --days 30

lint:
	poetry run ruff check src/ tests/

format:
	poetry run black src/ tests/ scripts/

clean:
	rm -rf output/week_*
	rm -rf logs/*.log
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

vllm-start:
	@echo "Start vLLM server with:"
	@echo ""
	@echo "python -m vllm.entrypoints.openai.api_server \\"
	@echo "  --model meta-llama/Llama-3.1-8B-Instruct \\"
	@echo "  --host 0.0.0.0 \\"
	@echo "  --port 8000 \\"
	@echo "  --dtype auto \\"
	@echo "  --max-model-len 4096 \\"
	@echo "  --gpu-memory-utilization 0.9"
