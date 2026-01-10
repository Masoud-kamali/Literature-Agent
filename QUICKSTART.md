# Quick Start Guide

Get up and running with the Literature Agent in 5 minutes.

**What it does**: Automatically finds 2 research papers + 1 community tool about 3D Gaussian Splatting, generates attractive LinkedIn-ready descriptions with smooth flow and precise metrics.

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
# Run with defaults (2 papers + 1 tool from last 7 days)
poetry run python scripts/run_weekly.py

# Or use Make
make run

# Custom date range
poetry run python scripts/run_weekly.py --days 14

# Clear ledger for fresh run (testing)
python scripts/clear_ledger.py
```

**What happens**:
1. Fetches 2 papers from arXiv/OpenAlex/CVF
2. Fetches 1 tool from Reddit (r/PlayCanvas, r/GaussianSplatting)
3. Generates 3-sentence descriptions with smooth transitions
4. Reflection agent improves quality (Critic → Reviser)
5. Saves to `output/week_YYYY_MM_DD/`

## Check Outputs

Results are in `output/week_YYYY_MM_DD/`:

```bash
# View markdown report (LinkedIn post included)
cat output/week_*/weekly_report.md

# List generated JSONs (2 papers + 1 Reddit post)
ls output/week_*/*.json
```

**Output format**: Each item gets a 3-sentence flowing paragraph:
- Sentence 1: Innovation/problem (starts with paper name)
- Sentence 2: Method (smooth transition: "The approach...")
- Sentence 3: Precise results (includes metrics: "30% fewer artifacts")

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

## Configuration

**Change output format** (`.env` or `src/config.py`):
```bash
OUTPUT_FORMAT=2_papers_1_tool   # Default: 2 papers + 1 tool
# or
OUTPUT_FORMAT=3_papers           # 3 papers only (no Reddit)
```

**Change subreddits**:
```bash
REDDIT_SUBREDDITS=["PlayCanvas", "GaussianSplatting", "YourSubreddit"]
```

## Next Steps

- Read full [README.md](README.md) for detailed configuration
- Check [REDDIT_FEATURE.md](REDDIT_FEATURE.md) for Reddit integration details
- Customise prompts in `src/llm/prompts.py`
- Adjust search keywords in `src/config.py`

## Support

Questions? Check the README or open an issue.
