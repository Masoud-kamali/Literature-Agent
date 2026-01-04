"""CSV ledger for tracking processed papers."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from loguru import logger

from src.config import settings


class PaperLedger:
    """
    Manages the CSV ledger of processed papers.

    The ledger tracks all papers that have been processed to prevent duplicates.
    """

    FIELDNAMES = [
        "canonical_id",
        "source",
        "arxiv_id",
        "doi",
        "title",
        "authors",
        "venue",
        "year",
        "url",
        "discovered_date",
        "processed_date",
        "model_name",
        "abstract_rewrite",
        "problem_solved",
        "linkedin_post",
    ]

    def __init__(self, ledger_path: Path = None):
        """
        Initialise ledger.

        Args:
            ledger_path: Path to CSV file (defaults to config path)
        """
        self.ledger_path = ledger_path or settings.ledger_path
        self.processed_ids: Set[str] = set()
        self.ledger_rows: List[Dict] = []

        # Ensure parent directory exists
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing ledger
        self._load()

    def _load(self):
        """Load existing ledger from CSV."""
        if not self.ledger_path.exists():
            logger.info(f"Ledger file not found, will create new: {self.ledger_path}")
            return

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.ledger_rows.append(row)
                    canonical_id = row.get("canonical_id")
                    if canonical_id:
                        self.processed_ids.add(canonical_id)

            logger.info(f"Loaded {len(self.processed_ids)} processed papers from ledger")

        except Exception as e:
            logger.error(f"Failed to load ledger: {e}")
            raise

    def is_processed(self, canonical_id: str) -> bool:
        """
        Check if a paper has already been processed.

        Args:
            canonical_id: Canonical identifier for the paper

        Returns:
            True if already processed
        """
        return canonical_id in self.processed_ids

    def add_entry(
        self,
        paper_dict: Dict,
        model_name: str,
        abstract_rewrite: str,
        problem_solved: str,
        linkedin_post: str,
    ):
        """
        Add a new processed paper to the ledger (in memory).

        Args:
            paper_dict: Paper metadata dictionary
            model_name: Name of LLM model used
            abstract_rewrite: Generated abstract rewrite
            problem_solved: Generated problem statement
            linkedin_post: Generated LinkedIn post
        """
        now = datetime.now().isoformat()

        entry = {
            "canonical_id": paper_dict.get("canonical_id"),
            "source": paper_dict.get("source"),
            "arxiv_id": paper_dict.get("arxiv_id", ""),
            "doi": paper_dict.get("doi", ""),
            "title": paper_dict.get("title"),
            "authors": paper_dict.get("authors", ""),
            "venue": paper_dict.get("venue", ""),
            "year": paper_dict.get("year", ""),
            "url": paper_dict.get("url", ""),
            "discovered_date": now,
            "processed_date": now,
            "model_name": model_name,
            "abstract_rewrite": abstract_rewrite,
            "problem_solved": problem_solved,
            "linkedin_post": linkedin_post,
        }

        self.ledger_rows.append(entry)
        self.processed_ids.add(entry["canonical_id"])

    def save(self):
        """Write ledger to CSV file."""
        try:
            # Write to temp file first, then atomic rename
            temp_path = self.ledger_path.with_suffix(".tmp")

            with open(temp_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                writer.writerows(self.ledger_rows)

            # Atomic rename
            temp_path.replace(self.ledger_path)

            logger.info(f"Saved ledger with {len(self.ledger_rows)} entries")

        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")
            raise

    def get_new_papers_count(self) -> int:
        """Get count of papers added in current session."""
        return len([r for r in self.ledger_rows if r.get("processed_date") == r.get("discovered_date")])
