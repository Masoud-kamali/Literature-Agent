# Quick Start Guide

Get up and running with the Literature Agent in 5 minutes.

## Prerequisites

- Linux GPU server with CUDA
- Python 3.10+
- Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)

## Installation

```bash
# 1. Navigate to project
cd literature-agent

# 2. Install dependencies
poetry install

# 3. Copy environment template
cp .env.example .env

# 4. Edit .env with your email for OpenAlex
nano .env  # Change OPENALEX_MAILTO to your email
```

## Start vLLM Server

In a **separate terminal** (or tmux/screen session):

```bash
# Install vLLM if not already installed
pip install vllm

# Start server (8B model - ~16GB VRAM required)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

**First run**: This downloads model weights (~8-16GB). Subsequent runs are instant.

**Verify it's running**:
```bash
curl http://localhost:8000/v1/models
```

## Run the Agent

```bash
# Run with defaults (last 7 days)
poetry run python scripts/run_weekly.py

# Or use Make
make run
```

## Check Outputs

Results are in `output/week_YYYY_MM_DD/`:

```bash
# View markdown report
cat output/week_*/weekly_report.md

# List generated JSONs
ls output/week_*/*.json
```

## Schedule Weekly Runs

```bash
# Edit crontab
crontab -e

# Add this line (runs Mondays at 9 AM)
0 9 * * 1 cd /path/to/literature-agent && /usr/local/bin/poetry run python scripts/run_weekly.py >> logs/cron.log 2>&1
```

**Important**: Ensure vLLM server runs as a systemd service or in a persistent tmux session.

## Common Commands

```bash
# Run tests
make test

# Process last 30 days (backfill)
poetry run python scripts/backfill.py --days 30

# Debug mode
poetry run python scripts/run_weekly.py --log_level DEBUG

# Custom lookback
poetry run python scripts/run_weekly.py --days 14 --max_results 100
```

## Troubleshooting

**"Connection refused"**
- vLLM not running → Check with `curl http://localhost:8000/v1/models`

**"CUDA out of memory"**
- Use smaller model or reduce `--max-model-len`

**"No papers found"**
- Check internet connection
- Increase `--days` parameter
- Verify search keywords in `src/config.py`

## Next Steps

- Read full [README.md](README.md) for detailed configuration
- View [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) for sample outputs
- Customise prompts in `src/llm/prompts.py`
- Adjust search keywords in `src/config.py`

## Support

Questions? Check the README or open an issue.
