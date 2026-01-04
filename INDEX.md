# Literature Agent - Complete Index

## 📚 Quick Navigation

### Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. **[README.md](README.md)** - Complete documentation
3. **[EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)** - See what it produces

### Reference
- **[PROMPTS.md](PROMPTS.md)** - All LLM prompts with customisation notes
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Architecture and data flow
- **[DELIVERABLES.md](DELIVERABLES.md)** - Requirements checklist

### Configuration
- **[.env.example](.env.example)** - Environment variables template
- **[cron.example](cron.example)** - Scheduling examples
- **[pyproject.toml](pyproject.toml)** - Dependencies

---

## 📖 Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| **README.md** | Complete setup, usage, and troubleshooting | All users |
| **QUICKSTART.md** | 5-minute installation and first run | New users |
| **EXAMPLE_OUTPUT.md** | Sample papers with generated outputs | Evaluators |
| **PROMPTS.md** | All prompt templates with engineering notes | Customisers |
| **PROJECT_STRUCTURE.md** | Architecture, data flow, module descriptions | Developers |
| **DELIVERABLES.md** | Requirements checklist and verification | Project managers |
| **INDEX.md** | This file - comprehensive navigation | All users |

---

## 🗂️ Directory Structure

```
literature-agent/
├── 📄 Configuration Files (7)
│   ├── pyproject.toml              Poetry dependencies
│   ├── .env.example                Environment template
│   ├── .gitignore                  Git ignore rules
│   ├── pytest.ini                  Test configuration
│   ├── Makefile                    Convenience commands
│   ├── LICENSE                     MIT License
│   └── cron.example                Scheduling examples
│
├── 📚 Documentation (7)
│   ├── README.md                   Main documentation
│   ├── QUICKSTART.md               Quick start guide
│   ├── EXAMPLE_OUTPUT.md           Sample outputs
│   ├── PROMPTS.md                  Prompt reference
│   ├── PROJECT_STRUCTURE.md        Architecture
│   ├── DELIVERABLES.md             Requirements checklist
│   └── INDEX.md                    This file
│
├── 📦 Source Code (src/)
│   ├── config.py                   Pydantic settings (203 lines)
│   │
│   ├── clients/                    Data source clients (3 files, 494 lines)
│   │   ├── arxiv_client.py         arXiv API client
│   │   ├── openalex_client.py      OpenAlex API client
│   │   └── cvf_client.py           CVF HTML scraper
│   │
│   ├── dedupe/                     Deduplication (2 files, 196 lines)
│   │   ├── normalise.py            Title normalisation + hashing
│   │   └── ledger.py               CSV ledger management
│   │
│   ├── llm/                        LLM integration (2 files, 261 lines)
│   │   ├── vllm_chat.py            vLLM OpenAI-compatible client
│   │   └── prompts.py              All prompt templates
│   │
│   ├── agents/                     Orchestration (2 files, 439 lines)
│   │   ├── pipeline.py             Main pipeline orchestration
│   │   └── reflection.py           LangGraph reflection agent
│   │
│   ├── output/                     Writers (1 file, 155 lines)
│   │   └── writer.py               JSON and markdown writers
│   │
│   └── publish/                    Publishing (1 file, 131 lines)
│       └── linkedin.py             LinkedIn dry-run stub
│
├── 🔧 Scripts (3)
│   ├── run_weekly.py               Main CLI runner (135 lines)
│   ├── backfill.py                 Historical backfill (99 lines)
│   └── verify_setup.py             Setup verification (251 lines)
│
├── 🧪 Tests (3)
│   ├── test_normalise.py           Normalisation tests (95 lines)
│   ├── test_ledger.py              Ledger tests (112 lines)
│   └── test_mock_run.py            End-to-end mock (125 lines)
│
└── 📁 Runtime Directories (created at runtime)
    ├── data/                       Ledger storage
    ├── output/                     Generated reports
    └── logs/                       Application logs
```

---

## 🔑 Key Files by Task

### Installation & Setup
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Install: `poetry install`
3. Copy [.env.example](.env.example) to `.env`
4. Verify: `poetry run python scripts/verify_setup.py`

### Running the Agent
- **Weekly run**: `scripts/run_weekly.py`
- **Backfill**: `scripts/backfill.py`
- **Config**: `src/config.py`

### Understanding Outputs
- **What it produces**: [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)
- **Output writer**: `src/output/writer.py`
- **Ledger format**: `src/dedupe/ledger.py`

### Customisation
- **Change prompts**: `src/llm/prompts.py` + [PROMPTS.md](PROMPTS.md)
- **Add data sources**: `src/clients/` (see existing clients as templates)
- **Modify workflow**: `src/agents/pipeline.py`
- **Adjust reflection**: `src/agents/reflection.py`

### Testing & Validation
- **Unit tests**: `tests/test_*.py`
- **Run tests**: `make test` or `poetry run pytest`
- **Verify setup**: `scripts/verify_setup.py`

### Scheduling
- **Cron setup**: [cron.example](cron.example)
- **Systemd service**: See [cron.example](cron.example) for vLLM service

---

## 🎯 Common Tasks

### Task: First Run
```bash
# Files involved
1. QUICKSTART.md          # Instructions
2. .env.example           # Copy to .env
3. scripts/verify_setup.py # Verify setup
4. scripts/run_weekly.py  # Run agent
5. output/week_*/         # Check outputs
```

### Task: Change Search Keywords
```bash
# Files to edit
1. src/config.py          # Update search_keywords list
2. (optional) src/clients/arxiv_client.py  # Verify query format
```

### Task: Use Different Model
```bash
# Files to edit
1. .env                   # Set VLLM_MODEL_NAME
2. (restart vLLM)         # Load new model
```

### Task: Modify Output Format
```bash
# Files to edit
1. src/llm/prompts.py              # Add new prompt
2. src/agents/pipeline.py          # Call new prompt
3. src/agents/reflection.py        # Update critic
4. src/dedupe/ledger.py            # Add ledger column
5. src/output/writer.py            # Update output format
```

### Task: Add New Data Source
```bash
# Files to create/edit
1. src/clients/new_source_client.py  # Implement client
2. src/agents/pipeline.py            # Add to retrieve_all_papers()
3. tests/test_new_source.py          # Add tests
```

### Task: Deploy to Production
```bash
# Files involved
1. cron.example           # Setup cron job
2. (create systemd service for vLLM)
3. .env                   # Production config
4. scripts/run_weekly.py  # Scheduled script
5. logs/                  # Monitor logs
```

## 🔍 Finding Things

### "Where is the code that..."

| Task | File | Function/Class |
|------|------|----------------|
| Fetches arXiv papers | `src/clients/arxiv_client.py` | `ArxivClient.search_papers()` |
| Checks for duplicates | `src/dedupe/ledger.py` | `PaperLedger.is_processed()` |
| Calls the LLM | `src/llm/vllm_chat.py` | `VLLMChatClient.chat_completion()` |
| Runs reflection | `src/agents/reflection.py` | `ReflectionAgent.reflect()` |
| Writes outputs | `src/output/writer.py` | `OutputWriter.write_all()` |
| Orchestrates pipeline | `src/agents/pipeline.py` | `LiteraturePipeline.run()` |
| Normalises titles | `src/dedupe/normalise.py` | `normalise_title()` |
| Defines prompts | `src/llm/prompts.py` | (all prompt constants) |

### "Where are the prompts for..."

| Output Type | Constant | File |
|-------------|----------|------|
| Abstract rewrite | `ABSTRACT_REWRITE_PROMPT` | `src/llm/prompts.py` |
| Problem statement | `PROBLEM_STATEMENT_PROMPT` | `src/llm/prompts.py` |
| LinkedIn post | `LINKEDIN_POST_PROMPT` | `src/llm/prompts.py` |
| Critic | `CRITIC_PROMPT` | `src/llm/prompts.py` |
| Reviser | `REVISER_PROMPT` | `src/llm/prompts.py` |

### "Where are the tests for..."

| Component | Test File |
|-----------|-----------|
| Title normalisation | `tests/test_normalise.py` |
| Ledger operations | `tests/test_ledger.py` |
| Full pipeline | `tests/test_mock_run.py` |

---

## 🛠️ Development Workflow

### Making Changes

1. **Edit code**: Choose file from structure above
2. **Format**: `make format` (Black)
3. **Lint**: `make lint` (Ruff)
4. **Test**: `make test` (Pytest)
5. **Type check**: `poetry run mypy src/`
6. **Run**: `poetry run python scripts/run_weekly.py`

### Adding Features

1. **Plan**: Review [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. **Implement**: Add/modify files in `src/`
3. **Test**: Add tests in `tests/`
4. **Document**: Update relevant .md files
5. **Verify**: Run `scripts/verify_setup.py`

---

## 📞 Getting Help

### Documentation Order

1. **[QUICKSTART.md](QUICKSTART.md)** - Start here
2. **[README.md](README.md)** - Detailed guide
3. **[EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)** - See examples
4. **[PROMPTS.md](PROMPTS.md)** - Prompt reference
5. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Architecture

### Troubleshooting

| Problem | Check | File |
|---------|-------|------|
| vLLM connection error | Server running? | README.md "Troubleshooting" |
| No papers found | Internet + keywords | src/config.py `search_keywords` |
| Import errors | Dependencies installed? | pyproject.toml |
| Test failures | Environment correct? | pytest.ini |
| Wrong outputs | Check prompts | PROMPTS.md |

### Common Commands

```bash
# Setup
poetry install
poetry run python scripts/verify_setup.py

# Run
poetry run python scripts/run_weekly.py
poetry run python scripts/backfill.py --days 30

# Test
make test
poetry run pytest tests/ -v --cov=src

# Maintain
make format
make lint
make clean
```

---

## 🎓 Learning Resources

### Understanding the Architecture
1. Read [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) data flow
2. Review `src/agents/pipeline.py` orchestration
3. Study `src/agents/reflection.py` LangGraph implementation

### Understanding the Prompts
1. Read [PROMPTS.md](PROMPTS.md) engineering notes
2. Review `src/llm/prompts.py` templates
3. Check [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) results

### Understanding Deduplication
1. Read `src/dedupe/normalise.py` algorithm
2. Study `src/dedupe/ledger.py` CSV management
3. Run `tests/test_normalise.py` to see examples

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] Run `poetry run python scripts/verify_setup.py`
- [ ] All tests pass: `make test`
- [ ] vLLM server configured as systemd service
- [ ] `.env` file created with real email
- [ ] Cron job configured (see [cron.example](cron.example))
- [ ] Log rotation configured
- [ ] Outputs directory has adequate storage
- [ ] First manual run successful
- [ ] Review [README.md](README.md) troubleshooting section

---

## 📈 Version History

- **v0.1.0** (Jan 2024): Initial production release
  - Multi-source retrieval (arXiv, OpenAlex, CVF)
  - vLLM integration with reflection agent
  - Complete deduplication system
  - Comprehensive documentation

---
