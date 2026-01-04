# Literature Agent for 3D Gaussian Splatting

An autonomous research agent that discovers, analyzes, and generates publication-ready summaries of new research papers on 3D Gaussian Splatting using locally-hosted LLMs via vLLM.

## Features

- **Multi-source Retrieval**: Fetches papers from arXiv, OpenAlex, and CVF Open Access (CVPR/ICCV/ECCV)
- **Local LLM Integration**: Uses vLLM with OpenAI-compatible API (Llama-3.1-8B-Instruct)
- **Reflection Agent**: LangGraph-based critique and revision for quality control
- **Smart Deduplication**: CSV ledger with unlimited retry until target papers found
- **Australian English**: All outputs in Australian English with academic tone
- **Combined LinkedIn Posts**: Generates single posts featuring 3 papers with structured format
- **Production Ready**: Robust error handling, retry logic, and rate limiting

## Generated Outputs

The agent generates a combined LinkedIn post titled "3D Gaussian Splatting — Weekly Literature Update" featuring 3 papers:

For each paper:
1. **Technical Abstract** (brief, 1-2 sentences highlighting key contribution)
2. **Problem Addressed** (brief, 1-2 sentences explaining what problem it solves)
3. **Metadata**: Title, authors, and URL

All outputs undergo reflection: a critic agent reviews for factuality, specificity, and style, then a reviser applies improvements if needed.

## Architecture

```
literature-agent/
├── src/
│   ├── config.py              # Pydantic settings
│   ├── clients/               # Data source clients
│   │   ├── arxiv_client.py
│   │   ├── openalex_client.py
│   │   └── cvf_client.py
│   ├── dedupe/                # Deduplication logic
│   │   ├── ledger.py          # CSV ledger management
│   │   └── normalise.py       # Title normalisation + hashing
│   ├── llm/                   # LLM integration
│   │   ├── vllm_chat.py       # OpenAI-compatible vLLM client
│   │   └── prompts.py         # All prompt templates
│   ├── agents/                # Agent orchestration
│   │   ├── pipeline.py        # Main orchestration
│   │   └── reflection.py      # LangGraph reflection agent
│   ├── output/                # Output writers
│   │   └── writer.py
│   └── publish/               # Publishing stubs
│       └── linkedin.py
├── scripts/
│   ├── run_weekly.py          # Main CLI runner
│   └── backfill.py            # Historical backfill
├── tests/                     # Unit tests
├── data/                      # Ledger storage
├── output/                    # Generated reports
└── logs/                      # Application logs
```

## Installation

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (for vLLM)
- Poetry (package manager)

### Setup Steps

1. **Clone and Install Dependencies**

```bash
git clone https://github.com/Masoud-kamali/Literature-Agent.git
cd Literature-Agent
poetry install
```

2. **Configure Environment Variables** (optional)

Create a `.env` file:

```bash
# vLLM settings
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
VLLM_TEMPERATURE=0.7
VLLM_MAX_TOKENS=1024

# OpenAlex polite pool (recommended)
OPENALEX_MAILTO=your.email@example.edu.au

# LinkedIn (dry-run by default)
LINKEDIN_DRY_RUN=true

# Logging
LOG_LEVEL=INFO
```

3. **Start vLLM Server**

The agent requires a running vLLM server. Use the provided startup script:

```bash
# Create conda/mamba environment for vLLM
mamba create -n vllm python=3.10 -y
mamba activate vllm
pip install vllm

# Start vLLM server (script included)
bash scripts/setup/start_vllm.sh
```

Or manually:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.75 \
  --disable-custom-all-reduce
```

**Note**: The first run will download the model weights (~16GB for 8B model). You must have access to the Llama model on HuggingFace.

4. **Authenticate with HuggingFace** (required for Llama models)

```bash
pip install huggingface_hub
huggingface-cli login
# Enter your HuggingFace token when prompted
```

5. **Verify vLLM is Running**

```bash
curl http://localhost:8000/v1/models
```

You should see JSON output with your model name.

## Usage

### Basic Run

Process papers from the last 7 days:

```bash
poetry run python scripts/run_weekly.py
```

The agent will:
1. Fetch papers from arXiv, OpenAlex, and CVF conferences
2. Deduplicate against the ledger
3. Keep fetching with increasing batch sizes until 3 new papers are found
4. Generate technical abstracts and problem statements
5. Apply reflection (critique and revision)
6. Create a combined LinkedIn post with all 3 papers
7. Save outputs to `output/week_YYYY_MM_DD/`

### Custom Lookback Period

Process papers from the last 14 days:

```bash
poetry run python scripts/run_weekly.py --days 14
```

**Note**: CVF conferences are filtered by date range. For example, with `--days 30`, only years from the last 30 days are checked (e.g., if running in January 2026, only 2026 and 2025 conferences are searched).

### Increase Initial Batch Size

Start with larger batch (default is from config):

```bash
poetry run python scripts/run_weekly.py --max_results 100
```

### Debug Mode

Run with detailed logging:

```bash
poetry run python scripts/run_weekly.py --log_level DEBUG
```

## Outputs

After each run, outputs are saved to `output/week_YYYY_MM_DD/`:

- **`weekly_report.md`**: Combined markdown report with:
  - Individual sections for each paper (abstract rewrite, problem statement, individual LinkedIn post)
  - **Combined LinkedIn Post** section with all 3 papers in publication-ready format
- **Individual JSON files**: One per paper with all metadata and generated content

Example Combined LinkedIn Post Format:

```
3D Gaussian Splatting — Weekly Literature Update

## Paper 1: [Title]
**Authors**: [Authors list]
**URL**: [URL]

### Technical Abstract
[1-2 sentences describing the key contribution]

### Problem Addressed
[1-2 sentences explaining what problem it solves]

## Paper 2: [Title]
...

## Paper 3: [Title]
...

#ComputerVision #3DGaussianSplatting #MachineLearning #Research
```

Example JSON output:

```json
{
  "canonical_id": "2401.12345",
  "source": "arxiv",
  "title": "3D Gaussian Splatting for Real-Time Rendering",
  "authors": "Smith, A.; Johnson, B.",
  "year": 2024,
  "url": "https://arxiv.org/pdf/2401.12345.pdf",
  "abstract_rewrite": "This paper introduces...",
  "problem_solved": "Traditional rendering methods...",
  "linkedin_post": "New Research Alert...",
  "model_name": "meta-llama/Llama-3.1-8B-Instruct"
}
```

## Deduplication

The agent maintains a CSV ledger at `data/ledger.csv` with all processed papers. Each paper is identified by:

1. **arXiv ID** (if from arXiv)
2. **DOI** (if available from OpenAlex)
3. **Stable hash** of normalized title (for CVF papers)

On each run, the agent:
- Loads the ledger into memory
- Skips any paper already in the ledger
- **Keeps fetching with increasing batch sizes** until 3 new papers are found (no attempt limit)
- Appends new papers after successful processing
- Saves the ledger atomically

This ensures:
- No duplicates across runs
- Always generates exactly 3 new papers (unless source is exhausted)
- Efficient handling of high-duplication scenarios

## Rate Limiting and Polite Crawling

The agent respects rate limits for all data sources:

- **arXiv**: 3-second delay between requests (configurable)
- **OpenAlex**: 0.1-second delay + polite pool `mailto` parameter
- **CVF**: 2-second delay between page requests

All HTTP calls use exponential backoff retry logic (3 attempts by default).

## Reflection Agent

The reflection process (powered by LangGraph):

1. **Draft Generation**: Generate initial outputs using prompts
2. **Critic Node**: LLM reviews outputs for:
   - Factuality (no claims beyond abstract)
   - Specificity (technical details preserved)
   - Novelty framing (contribution clarity)
   - Style (Australian English, academic tone)
   - Length constraints
3. **Decision**: If score ≥ 8/10, accept; otherwise proceed to revision
4. **Reviser Node**: Apply critic's suggested actions to improve outputs
5. **Output**: Return final refined outputs

The critic uses lower temperature (0.3) for consistent evaluation.

## Testing

Run unit tests:

```bash
poetry run pytest tests/ -v
```

Run with coverage:

```bash
poetry run pytest tests/ --cov=src --cov-report=html
```

Tests cover:
- Title normalisation and hashing
- Ledger operations (add, save, load, dedupe)
- Mock end-to-end pipeline run

## LinkedIn Publishing

By default, the agent runs in **dry-run mode**: it generates LinkedIn posts but does not publish them.

To enable actual posting:

1. Create a LinkedIn App at https://www.linkedin.com/developers/apps
2. Configure OAuth 2.0 and obtain access token
3. Implement the OAuth flow in `src/publish/linkedin.py`
4. Set `LINKEDIN_DRY_RUN=false` in your `.env`

For detailed LinkedIn API integration, see the instructions printed by:

```bash
poetry run python scripts/run_weekly.py
```

## Configuration Reference

Key settings in `src/config.py` (overridable via environment variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | vLLM API endpoint |
| `VLLM_MODEL_NAME` | `meta-llama/Llama-3.1-8B-Instruct` | Model name |
| `VLLM_TEMPERATURE` | `0.7` | Sampling temperature |
| `VLLM_MAX_TOKENS` | `1024` | Max tokens per generation |
| `OPENALEX_MAILTO` | `researcher@example.edu.au` | Polite pool email |
| `DEFAULT_DAYS_BACK` | `7` | Default lookback period |
| `MAX_RESULTS_PER_SOURCE` | `50` | Max papers per source |
| `REFLECTION_MAX_ITERATIONS` | `1` | Reflection cycles |
| `LINKEDIN_DRY_RUN` | `true` | Dry-run mode for posts |

## Prompts

All prompts are defined in `src/llm/prompts.py`:

- **SYSTEM_PROMPT**: Base system message (academic writer persona)
- **ABSTRACT_REWRITE_PROMPT**: Technical abstract rewrite
- **PROBLEM_STATEMENT_PROMPT**: Problem being solved
- **LINKEDIN_POST_PROMPT**: LinkedIn-ready post
- **CRITIC_PROMPT**: Reflection critic evaluation
- **REVISER_PROMPT**: Reflection revision application

These prompts enforce Australian English spelling and academic tone.

## Troubleshooting

### vLLM Connection Errors

**Problem**: `Connection refused` or timeout errors

**Solutions**:
- Verify vLLM server is running: `curl http://localhost:8000/v1/models`
- Check firewall rules if running on remote server
- Ensure correct `VLLM_BASE_URL` in config

### Out of Memory (OOM) Errors

**Problem**: vLLM crashes with CUDA OOM

**Solutions**:
- Use smaller model (e.g., 8B instead of 70B)
- Reduce `--max-model-len` in vLLM startup
- Lower `--gpu-memory-utilization` (default 0.9)
- Enable tensor parallelism for multi-GPU

### No Papers Retrieved

**Problem**: Agent reports 0 papers found

**Solutions**:
- Verify internet connectivity
- Check if date range is too narrow (increase `--days`)
- Verify search keywords in `config.py` are relevant
- Check API status for arXiv/OpenAlex

### JSON Parsing Errors in Reflection

**Problem**: Reflection agent fails to parse LLM output

**Solutions**:
- This is expected occasionally with open models
- The agent has fallback logic (accepts draft outputs)
- Try a more capable model (e.g., 70B or Llama-3.3-70B-Instruct)
- Adjust prompts in `src/llm/prompts.py` for your model

## Example Run Output

```
2024-01-15 09:00:00 | INFO     | Starting Literature Agent Pipeline
2024-01-15 09:00:05 | INFO     | Retrieved 45 papers from arXiv
2024-01-15 09:00:08 | INFO     | Retrieved 23 papers from OpenAlex
2024-01-15 09:00:12 | INFO     | Retrieved 8 papers from CVF
2024-01-15 09:00:12 | INFO     | Filtered to 12 new papers (skipped 64 duplicates)
2024-01-15 09:00:45 | INFO     | Generating outputs for: 3D Gaussian Splatting for Real-Time Rendering
2024-01-15 09:01:20 | INFO     | Reflection: Running critic node
2024-01-15 09:01:35 | INFO     | Critique score: 9/10, 0 actions
2024-01-15 09:01:35 | INFO     | Accepting outputs (score=9, iteration=0)
2024-01-15 09:01:35 | INFO     | Completed processing: 3D Gaussian Splatting for Real-Time Rendering
...
2024-01-15 09:15:20 | INFO     | Pipeline complete: 12 papers processed
2024-01-15 09:15:21 | INFO     | Outputs written to: output/week_2024_01_15
```

## Dependencies

Core dependencies (managed by Poetry):

- **httpx**: Async HTTP client
- **beautifulsoup4 + lxml**: HTML parsing for CVF
- **feedparser**: arXiv API feed parsing
- **openai**: OpenAI-compatible client for vLLM
- **langgraph**: Reflection agent state machine
- **pydantic**: Configuration and validation
- **loguru**: Structured logging
- **tenacity**: Retry logic
- **pandas**: Ledger CSV handling

## Contributing

To extend the agent:

1. **Add new data sources**: Implement client in `src/clients/`
2. **Modify prompts**: Edit templates in `src/llm/prompts.py`
3. **Customise reflection**: Adjust graph in `src/agents/reflection.py`
4. **Add output formats**: Extend `src/output/writer.py`

## License

Apache License 2.0 - see [LICENSE](LICENSE) file.

## Citation

If you use this agent in your research workflow, please cite:

```bibtex
@software{literature_agent_2026,
  title={Literature Agent for 3D Gaussian Splatting},
  author={Kamali, Masoud},
  year={2026},
  url={https://github.com/Masoud-kamali/Literature-Agent}
}
```

## Acknowledgements

- vLLM team for efficient local inference
- OpenAlex for open academic data
- arXiv for open access preprints
- CVF for conference open access

---

**Questions or Issues?** Please open an issue on GitHub or contact the maintainers.
