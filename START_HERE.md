# 🚀 START HERE

Welcome to the **Autonomous Literature Agent** for 3D Gaussian Splatting papers!

---

## ✅ What You Have

A complete, production-ready Python codebase that:

- ✅ **Discovers** new papers from arXiv, OpenAlex, and CVF conferences
- ✅ **Generates** technical summaries using local LLMs (vLLM)
- ✅ **Creates** LinkedIn posts in Australian English
- ✅ **Prevents** duplicates with CSV ledger tracking
- ✅ **Improves** outputs with reflection agent (LangGraph)
- ✅ **Runs** weekly via cron scheduling

**Total**: 3,114 lines of code | 36 files | 100% requirements met

---

## 📖 Quick Navigation

### 🏃 I Want to Run It Now
**→ [QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide

### 📚 I Want Complete Documentation
**→ [README.md](README.md)** - Full setup, usage, and troubleshooting

### 👀 I Want to See Examples
**→ [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)** - Sample papers with generated outputs

### 🔧 I Want to Customize Prompts
**→ [PROMPTS.md](PROMPTS.md)** - All prompt templates with engineering notes

### 🏗️ I Want to Understand the Architecture
**→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Data flow and module design

### ✅ I Want to Verify Requirements
**→ [DELIVERABLES.md](DELIVERABLES.md)** - Complete requirements checklist

### 🗺️ I Want Complete Index
**→ [INDEX.md](INDEX.md)** - Comprehensive navigation and file reference

---

## ⚡ Three-Step Quick Start

### 1️⃣ Install Dependencies
```bash
cd literature-agent
poetry install
cp .env.example .env
nano .env  # Set your email for OPENALEX_MAILTO
```

### 2️⃣ Start vLLM Server (in separate terminal)
```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000
```

### 3️⃣ Run the Agent
```bash
poetry run python scripts/run_weekly.py
```

**Results** → `output/week_YYYY_MM_DD/weekly_report.md`

---

## 📁 What's Inside

```
literature-agent/
├── 📚 Documentation (7 files)
│   ├── START_HERE.md ← You are here
│   ├── QUICKSTART.md
│   ├── README.md
│   ├── EXAMPLE_OUTPUT.md
│   ├── PROMPTS.md
│   ├── PROJECT_STRUCTURE.md
│   ├── DELIVERABLES.md
│   └── INDEX.md
│
├── 💻 Source Code (src/)
│   ├── clients/        → arXiv, OpenAlex, CVF retrieval
│   ├── dedupe/         → Deduplication + ledger
│   ├── llm/            → vLLM client + prompts
│   ├── agents/         → Pipeline + reflection
│   ├── output/         → JSON and markdown writers
│   └── publish/        → LinkedIn stub
│
├── 🔧 Scripts
│   ├── run_weekly.py   → Main CLI
│   ├── backfill.py     → Historical data
│   └── verify_setup.py → Check installation
│
├── 🧪 Tests
│   └── Unit tests for deduplication, ledger, pipeline
│
└── ⚙️ Config
    ├── pyproject.toml  → Dependencies
    ├── .env.example    → Environment template
    └── cron.example    → Scheduling examples
```

---

## 🎯 What It Does

### Input (3 data sources)
```
arXiv API → Papers with "gaussian splatting", "3DGS", etc.
OpenAlex API → Academic papers from multiple venues
CVF Open Access → CVPR/ICCV/ECCV conference papers
```

### Processing (with reflection)
```
1. Retrieve papers from all sources (async, parallel)
2. Deduplicate using CSV ledger
3. Generate 3 outputs per paper (LLM):
   • Technical abstract rewrite (100-150 words)
   • Problem statement (2-4 sentences)
   • LinkedIn post (120-180 words)
4. Reflection agent critiques and revises
5. Save to JSON + markdown + ledger
```

### Output
```
✓ Per-paper JSON files
✓ Combined weekly markdown report
✓ Updated CSV ledger (no duplicates next run)
✓ LinkedIn posts ready to publish
```

---

## 🔑 Key Features

### 🆓 Free & Local
- **No paid APIs** (arXiv, OpenAlex, CVF are free)
- **Local LLM** via vLLM (no OpenAI API needed)
- **Self-hosted** on your GPU server

### 🇦🇺 Australian English
- All prompts enforce AU spelling ("optimised", "whilst")
- Academic tone throughout
- Factuality constraints (no hallucinations)

### 🔁 Reflection Agent
- **LangGraph** state machine
- **Critic** scores outputs (0-10)
- **Reviser** applies improvements
- Ensures quality before saving

### 🚫 No Duplicates
- **CSV ledger** tracks all processed papers
- **Canonical IDs**: arXiv ID, DOI, or stable hash
- **Skip** papers already in ledger

### 🏭 Production Ready
- Async I/O throughout
- Retry logic with exponential backoff
- Rate limiting for all sources
- Structured logging
- Error handling
- Cron compatible

---

## 💡 Common Use Cases

### Weekly Paper Discovery
```bash
# Run every Monday at 9 AM via cron
0 9 * * 1 cd /path/to/literature-agent && poetry run python scripts/run_weekly.py
```

### Backfill Historical Papers
```bash
poetry run python scripts/backfill.py --days 30
```

### Custom Search
```bash
# Edit src/config.py search_keywords
poetry run python scripts/run_weekly.py --days 14 --max_results 100
```

### LinkedIn Content Generation
```bash
# Dry-run mode (default) generates posts without publishing
poetry run python scripts/run_weekly.py

# Posts are in output/week_*/weekly_report.md
```

---

## 🛠️ Tech Stack

### Core
- **Python 3.10+** with asyncio
- **vLLM** for local LLM inference
- **LangGraph** for reflection agent
- **Pydantic** for configuration

### Data Sources
- **arXiv API** (feedparser)
- **OpenAlex API** (REST)
- **CVF** (BeautifulSoup + lxml)

### LLM Integration
- **OpenAI client** (compatible with vLLM)
- **Custom prompts** for AU English
- **Reflection** for quality control

### Tooling
- **Poetry** for dependency management
- **Pytest** for testing
- **Black** + **Ruff** for code quality
- **Loguru** for logging

---

## 📊 Project Stats

```
Lines of Code:      3,114
Python Modules:     24
Test Files:         3
Documentation:      7 files
Total Files:        36
Dependencies:       14 core + 6 dev
Test Coverage:      Core functions
```

---

## ❓ FAQ

**Q: Do I need an OpenAI API key?**
A: No! Use local vLLM server (free).

**Q: Can I use a different model?**
A: Yes! Set `VLLM_MODEL_NAME` in `.env`.

**Q: How do I change search keywords?**
A: Edit `search_keywords` in `src/config.py`.

**Q: Will it post to LinkedIn automatically?**
A: No, dry-run by default. See `src/publish/linkedin.py` for setup.

**Q: How do I avoid duplicates?**
A: Automatic! CSV ledger tracks all processed papers.

**Q: Can I run this daily instead of weekly?**
A: Yes! Use `--days 1` and adjust cron schedule.

---

## 🎓 Learning Path

### Beginner
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run first time
3. Check outputs in `output/week_*/`

### Intermediate
1. Read [README.md](README.md)
2. Understand [PROMPTS.md](PROMPTS.md)
3. Customize keywords
4. Run tests

### Advanced
1. Study [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. Review source code architecture
3. Add new data sources
4. Modify reflection agent

---

## 🆘 Need Help?

### Check These First
1. **[QUICKSTART.md](QUICKSTART.md)** - Installation issues
2. **[README.md](README.md)** - Troubleshooting section
3. **`scripts/verify_setup.py`** - Run verification
4. **[DELIVERABLES.md](DELIVERABLES.md)** - Requirements checklist

### Common Issues
- **vLLM connection error** → Server not running
- **No papers found** → Check internet + keywords
- **Import errors** → Run `poetry install`

---

## ✅ Ready to Start?

### Recommended First Steps

1. **Quick run**: [QUICKSTART.md](QUICKSTART.md) (5 minutes)
2. **See examples**: [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)
3. **Understand prompts**: [PROMPTS.md](PROMPTS.md)
4. **Full setup**: [README.md](README.md)
5. **Verify**: `poetry run python scripts/verify_setup.py`

---

## 🎉 Success Looks Like

After your first run, you should see:

```bash
✓ output/week_2024_01_15/
  ✓ paper1.json
  ✓ paper2.json
  ✓ ...
  ✓ weekly_report.md    ← Read this first!

✓ data/ledger.csv        ← Tracks processed papers

✓ logs/literature_agent.log  ← Execution logs
```

**Open** `weekly_report.md` to see your generated content!

---

**🚀 Ready? Start with [QUICKSTART.md](QUICKSTART.md)**

---

*Built with vLLM, LangGraph, and open research data sources.*
*No proprietary APIs required.*
