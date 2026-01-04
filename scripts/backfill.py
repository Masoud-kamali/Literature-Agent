#!/usr/bin/env python3
"""Backfill script for processing historical papers."""

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


def setup_logging(log_level: str = "INFO"):
    """Configure loguru logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=settings.log_format,
        level=log_level,
        colorize=True,
    )


async def main():
    """Backfill CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill historical 3D Gaussian Splatting papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Number of days to backfill (e.g., 30 for last month)",
    )

    parser.add_argument(
        "--max_results",
        type=int,
        default=200,
        help="Max results per source (default: 200)",
    )

    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=10,
        help="Process papers in batches of this size (default: 10)",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    logger.info(f"Starting backfill for last {args.days} days")

    try:
        pipeline = LiteraturePipeline()

        # Retrieve all papers
        all_papers = await pipeline.retrieve_all_papers(
            days_back=args.days,
            max_results=args.max_results,
        )

        # Filter new papers
        new_papers = pipeline.filter_new_papers(all_papers)

        if not new_papers:
            logger.info("No new papers to backfill")
            return 0

        logger.info(f"Backfilling {len(new_papers)} papers in batches of {args.batch_size}")

        # Process in batches
        results = []
        batch_size = args.batch_size

        for i in range(0, len(new_papers), batch_size):
            batch = new_papers[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(new_papers) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")

            for paper in batch:
                try:
                    result = await pipeline.process_paper(paper)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process paper: {e}")
                    continue

            # Save ledger after each batch
            pipeline.ledger.save()
            logger.info(f"Batch {batch_num} complete, ledger saved")

        # Write final outputs
        if results:
            writer = OutputWriter()
            output_paths = writer.write_all(results)
            logger.info(f"Outputs written to: {output_paths['markdown_report'].parent}")

        logger.info(f"Backfill complete: {len(results)} papers processed")

        return 0

    except Exception as e:
        logger.exception(f"Backfill failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
