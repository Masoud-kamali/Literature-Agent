#!/usr/bin/env python3
"""Weekly literature agent CLI runner."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.agents.pipeline import LiteraturePipeline
from src.config import settings
from src.output.writer import OutputWriter
from src.publish.linkedin import LinkedInPublisher


def setup_logging(log_level: str = None):
    """Configure loguru logging."""
    level = log_level or settings.log_level

    # Remove default handler
    logger.remove()

    # Add custom handler
    logger.add(
        sys.stderr,
        format=settings.log_format,
        level=level,
        colorize=True,
    )

    # Add file handler
    log_file = settings.base_dir / "logs" / "literature_agent.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format=settings.log_format,
        level=level,
        rotation="10 MB",
        retention="1 month",
    )


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous weekly literature agent for 3D Gaussian Splatting papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (7 days, 50 results per source)
  python scripts/run_weekly.py

  # Custom lookback period and max results
  python scripts/run_weekly.py --days 14 --max_results 100

  # Adjust log level
  python scripts/run_weekly.py --log_level DEBUG

Environment Variables (via .env or export):
  VLLM_BASE_URL           - vLLM server endpoint (default: http://localhost:8000/v1)
  VLLM_MODEL_NAME         - Model name in vLLM (default: meta-llama/Llama-3.1-8B-Instruct)
  OPENALEX_MAILTO         - Mailto for OpenAlex polite pool
  LINKEDIN_DRY_RUN        - Set to false to attempt real posting (default: true)
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help=f"Number of days to look back (default: {settings.default_days_back})",
    )

    parser.add_argument(
        "--max_results",
        type=int,
        default=None,
        help=f"Max results per source (default: {settings.max_results_per_source})",
    )

    parser.add_argument(
        "--log_level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level (default: {settings.log_level})",
    )

    parser.add_argument(
        "--no_publish",
        action="store_true",
        help="Skip LinkedIn publishing step (still generates posts)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    logger.info("Starting Literature Agent CLI")
    logger.info(f"vLLM endpoint: {settings.vllm_base_url}")
    logger.info(f"Model: {settings.vllm_model_name}")

    try:
        # Initialise pipeline
        pipeline = LiteraturePipeline()

        # Run pipeline
        results = await pipeline.run(
            days_back=args.days,
            max_results=args.max_results,
        )

        if not results:
            logger.info("No papers processed this run")
            return 0

        # Write outputs
        writer = OutputWriter()
        output_paths = writer.write_all(results)

        logger.info(f"Outputs written to: {output_paths['markdown_report'].parent}")

        # LinkedIn publishing
        if not args.no_publish:
            publisher = LinkedInPublisher()
            publisher.publish(results)

            if settings.linkedin_dry_run:
                publisher.print_instructions()

        logger.info("=" * 80)
        logger.info("Run complete!")
        logger.info(f"Processed: {len(results)} papers")
        logger.info(f"Markdown report: {output_paths['markdown_report']}")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
