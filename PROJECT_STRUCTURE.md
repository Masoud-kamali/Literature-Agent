# Project Structure

Complete file and directory structure for the Literature Agent.

```
literature-agent/
├── README.md                   # Main documentation
├── QUICKSTART.md               # Quick start guide
├── EXAMPLE_OUTPUT.md           # Sample outputs and run logs
├── PROMPTS.md                  # Complete prompt reference
├── PROJECT_STRUCTURE.md        # This file
├── LICENSE                     # MIT License
├── pyproject.toml              # Poetry dependencies and project metadata
├── pytest.ini                  # Pytest configuration
├── Makefile                    # Convenience commands
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── cron.example                # Crontab and systemd examples
│
├── src/                        # Main source code
│   ├── __init__.py
│   ├── config.py               # Pydantic settings with env support
│   │
│   ├── clients/                # Data source clients
│   │   ├── __init__.py
│   │   ├── arxiv_client.py     # arXiv API client with retry logic
│   │   ├── openalex_client.py  # OpenAlex API client
│   │   └── cvf_client.py       # CVF HTML scraper
│   │
│   ├── dedupe/                 # Deduplication system
│   │   ├── __init__.py
│   │   ├── normalise.py        # Title normalisation + hashing
│   │   └── ledger.py           # CSV ledger management
│   │
│   ├── llm/                    # LLM integration
│   │   ├── __init__.py
│   │   ├── vllm_chat.py        # vLLM OpenAI-compatible client
│   │   └── prompts.py          # All prompt templates
│   │
│   ├── agents/                 # Agent orchestration
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Main orchestration pipeline
│   │   └── reflection.py       # LangGraph reflection agent
│   │
│   ├── output/                 # Output writers
│   │   ├── __init__.py
│   │   └── writer.py           # JSON and markdown writers
│   │
│   └── publish/                # Publishing integrations
│       ├── __init__.py
│       └── linkedin.py         # LinkedIn dry-run stub
│
├── scripts/                    # CLI scripts
│   ├── run_weekly.py           # Main weekly runner
│   └── backfill.py             # Historical backfill script
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── test_normalise.py       # Title normalisation tests
│   ├── test_ledger.py          # Ledger operation tests
│   └── test_mock_run.py        # End-to-end mock test
│
├── data/                       # Data storage (created at runtime)
│   └── ledger.csv              # CSV ledger (git-ignored)
│
├── output/                     # Generated outputs (created at runtime)
│   └── week_YYYY_MM_DD/        # Weekly output directories (git-ignored)
│       ├── *.json              # Per-paper JSON files
│       └── weekly_report.md    # Combined markdown report
│
└── logs/                       # Application logs (created at runtime)
    ├── literature_agent.log    # Main log file (git-ignored)
    └── cron.log                # Cron job logs (git-ignored)
```

## Module Descriptions

### Core Modules

| Module | Purpose | Key Components |
|--------|---------|----------------|
| `config.py` | Configuration management | `Settings` class with Pydantic validation |
| `clients/` | External data retrieval | arXiv, OpenAlex, CVF clients with retry logic |
| `dedupe/` | Duplicate detection | Title normalisation, hashing, CSV ledger |
| `llm/` | LLM interaction | vLLM client, prompt templates |
| `agents/` | Agent logic | Pipeline orchestration, reflection graph |
| `output/` | Result persistence | JSON and markdown writers |
| `publish/` | External publishing | LinkedIn dry-run stub |

### Entry Points

| Script | Purpose |
|--------|---------|
| `scripts/run_weekly.py` | Weekly paper discovery and processing |
| `scripts/backfill.py` | Historical data backfill |

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry dependencies and build config |
| `pytest.ini` | Test configuration |
| `.env.example` | Environment variable template |
| `cron.example` | Cron and systemd examples |

### Documentation

| File | Content |
|------|---------|
| `README.md` | Complete setup and usage guide |
| `QUICKSTART.md` | 5-minute quick start |
| `EXAMPLE_OUTPUT.md` | Sample outputs with logs |
| `PROMPTS.md` | All prompt templates with notes |
| `PROJECT_STRUCTURE.md` | This file |

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐          │
│  │  arXiv   │  │ OpenAlex │  │  CVF Open Access │          │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘          │
└───────┼─────────────┼─────────────────┼────────────────────┘
        │             │                  │
        │             │                  │
        ▼             ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Retrieval Clients (src/clients/)               │
│   • Async HTTP with retry logic                            │
│   • Rate limiting and polite crawling                       │
│   • Structured paper objects                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Deduplication (src/dedupe/)                       │
│   • Load existing ledger                                    │
│   • Normalise titles and compute hashes                     │
│   • Filter out processed papers                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            LLM Generation (src/llm/)                        │
│   • vLLM OpenAI-compatible client                          │
│   • Generate: abstract, problem, LinkedIn post              │
│   • Concurrent generation for speed                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│       Reflection Agent (src/agents/reflection.py)           │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐         │
│   │  Critic  │ ───▶ │ Decision │ ───▶ │ Reviser  │         │
│   │  (score) │      │  (8/10?) │      │ (improve)│         │
│   └──────────┘      └──────────┘      └──────────┘         │
│                         │                                   │
│                         ▼ (score ≥ 8)                       │
│                    [Accept]                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Output Writers (src/output/)                     │
│   • Per-paper JSON files                                    │
│   • Combined weekly markdown report                         │
│   • Update CSV ledger                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         LinkedIn Publisher (src/publish/)                   │
│   • Dry-run mode: print payloads                           │
│   • Real mode: API integration (stub)                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### Async/Await Throughout
All I/O operations use `asyncio` for concurrent execution:
- Data source retrieval runs in parallel
- LLM generations for multiple outputs run concurrently
- Papers processed sequentially (to avoid overwhelming vLLM)

### Retry with Exponential Backoff
All HTTP calls use `tenacity` for robust error handling:
- Default: 3 retries with exponential backoff
- Configurable delays and timeouts
- Graceful degradation on failure

### State Machine (LangGraph)
Reflection agent uses LangGraph for structured flow:
- **Nodes**: Critic, Reviser
- **Edges**: Conditional (accept vs. revise)
- **State**: Preserves context across iterations

### Immutable Configuration
Pydantic settings with environment variable overrides:
- Type-safe configuration
- Clear defaults
- `.env` file support

### Atomic Ledger Updates
CSV ledger written atomically:
1. Write to `.tmp` file
2. Atomic rename on success
3. Prevents corruption on crashes

## File Counts

```
Python modules:     21
Test files:         3
Scripts:            2
Documentation:      6
Config files:       4
Total:              36 files
```

## Lines of Code (Approximate)

```
Source code (src/):     ~1,800 lines
Tests (tests/):         ~300 lines
Scripts (scripts/):     ~200 lines
Total Python:           ~2,300 lines
```

## Dependencies (pyproject.toml)

**Core**:
- pydantic, httpx, beautifulsoup4, openai, langgraph

**Utilities**:
- loguru, tenacity, feedparser, pandas

**Dev**:
- pytest, black, ruff, mypy

## Runtime Directories

These are created automatically at runtime:

```bash
data/              # Ledger storage
output/            # Weekly reports
logs/              # Application logs
```

Add to `.gitignore` to avoid committing generated files.

---

**Last Updated**: 2024-01-15
