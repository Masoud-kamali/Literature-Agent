#!/usr/bin/env python3
"""Setup verification script for Literature Agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import importlib.util


def check_color(passed: bool) -> str:
    """Return colored checkmark or X."""
    return "\033[92m✓\033[0m" if passed else "\033[91m✗\033[0m"


def check_imports():
    """Check that all required packages are importable."""
    print("\n" + "=" * 60)
    print("Checking Dependencies...")
    print("=" * 60)

    required_packages = [
        ("httpx", "HTTP client"),
        ("pydantic", "Configuration"),
        ("pydantic_settings", "Settings management"),
        ("loguru", "Logging"),
        ("tenacity", "Retry logic"),
        ("feedparser", "arXiv feed parsing"),
        ("bs4", "HTML parsing"),
        ("lxml", "XML parsing"),
        ("openai", "OpenAI client"),
        ("langgraph", "Reflection agent"),
        ("langchain_core", "LangChain core"),
        ("pandas", "CSV handling"),
        ("dateutil", "Date parsing"),
        ("pytest", "Testing"),
    ]

    all_passed = True

    for package, description in required_packages:
        spec = importlib.util.find_spec(package)
        passed = spec is not None
        all_passed = all_passed and passed
        status = check_color(passed)
        print(f"{status} {package:<25} {description}")

    return all_passed


def check_project_structure():
    """Check that all required files exist."""
    print("\n" + "=" * 60)
    print("Checking Project Structure...")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent

    required_files = [
        "src/config.py",
        "src/clients/arxiv_client.py",
        "src/clients/openalex_client.py",
        "src/clients/cvf_client.py",
        "src/dedupe/ledger.py",
        "src/dedupe/normalise.py",
        "src/llm/vllm_chat.py",
        "src/llm/prompts.py",
        "src/agents/pipeline.py",
        "src/agents/reflection.py",
        "src/output/writer.py",
        "src/publish/linkedin.py",
        "scripts/run_weekly.py",
        "scripts/backfill.py",
        "tests/test_normalise.py",
        "tests/test_ledger.py",
        "pyproject.toml",
        "README.md",
    ]

    all_passed = True

    for file_path in required_files:
        full_path = base_dir / file_path
        passed = full_path.exists()
        all_passed = all_passed and passed
        status = check_color(passed)
        print(f"{status} {file_path}")

    return all_passed


def check_directories():
    """Check that runtime directories exist."""
    print("\n" + "=" * 60)
    print("Checking Runtime Directories...")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent

    required_dirs = [
        "data",
        "output",
        "logs",
    ]

    all_passed = True

    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        passed = dir_path.exists() and dir_path.is_dir()
        all_passed = all_passed and passed
        status = check_color(passed)
        print(f"{status} {dir_name}/")

    return all_passed


async def check_vllm_connection():
    """Check connection to vLLM server."""
    print("\n" + "=" * 60)
    print("Checking vLLM Server Connection...")
    print("=" * 60)

    try:
        from src.config import settings
        import httpx

        url = f"{settings.vllm_base_url}/models"
        print(f"Testing connection to: {url}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            models = data.get("data", [])
            if models:
                print(f"{check_color(True)} vLLM server is running")
                print(f"  Available models: {[m.get('id') for m in models]}")
                return True
            else:
                print(f"{check_color(False)} No models found on vLLM server")
                return False

    except httpx.ConnectError:
        print(f"{check_color(False)} Cannot connect to vLLM server")
        print("  Make sure vLLM is running at:", settings.vllm_base_url)
        print("\n  Start vLLM with:")
        print("  python -m vllm.entrypoints.openai.api_server \\")
        print("    --model meta-llama/Llama-3.1-8B-Instruct \\")
        print("    --host 0.0.0.0 --port 8000")
        return False

    except Exception as e:
        print(f"{check_color(False)} Error checking vLLM: {e}")
        return False


def check_config():
    """Check configuration settings."""
    print("\n" + "=" * 60)
    print("Checking Configuration...")
    print("=" * 60)

    try:
        from src.config import settings

        config_items = [
            ("vLLM Base URL", settings.vllm_base_url),
            ("vLLM Model", settings.vllm_model_name),
            ("OpenAlex Mailto", settings.openalex_mailto),
            ("Default Days Back", settings.default_days_back),
            ("Max Results/Source", settings.max_results_per_source),
            ("LinkedIn Dry Run", settings.linkedin_dry_run),
        ]

        for name, value in config_items:
            print(f"{check_color(True)} {name:<25} {value}")

        # Check if using example email
        if settings.openalex_mailto == "researcher@example.edu.au":
            print(
                f"\n{check_color(False)} Warning: Using example email for OpenAlex"
            )
            print("  Please set OPENALEX_MAILTO in .env to your real email")
            return False

        return True

    except Exception as e:
        print(f"{check_color(False)} Error loading config: {e}")
        return False


async def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("Literature Agent - Setup Verification")
    print("=" * 60)

    results = {
        "Dependencies": check_imports(),
        "Project Structure": check_project_structure(),
        "Runtime Directories": check_directories(),
        "Configuration": check_config(),
        "vLLM Connection": await check_vllm_connection(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check_name, passed in results.items():
        status = check_color(passed)
        print(f"{status} {check_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "=" * 60)
        print("\033[92m✓ All checks passed! Ready to run.\033[0m")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. poetry run python scripts/run_weekly.py --days 7")
        print("  2. Check output/week_*/weekly_report.md")
        return 0
    else:
        print("\n" + "=" * 60)
        print("\033[91m✗ Some checks failed. Please fix and retry.\033[0m")
        print("=" * 60)
        print("\nTroubleshooting:")
        if not results["Dependencies"]:
            print("  - Run: poetry install")
        if not results["vLLM Connection"]:
            print("  - Start vLLM server (see README.md)")
        if not results["Configuration"]:
            print("  - Copy .env.example to .env and edit")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
