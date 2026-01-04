"""Tests for ledger functionality."""

import csv
import tempfile
from pathlib import Path

import pytest

from src.dedupe.ledger import PaperLedger


class TestPaperLedger:
    """Test paper ledger operations."""

    @pytest.fixture
    def temp_ledger_path(self):
        """Create temporary ledger file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_new_ledger_creation(self, temp_ledger_path):
        """Test creating a new ledger."""
        ledger = PaperLedger(ledger_path=temp_ledger_path)
        assert len(ledger.processed_ids) == 0
        assert len(ledger.ledger_rows) == 0

    def test_add_and_check_entry(self, temp_ledger_path):
        """Test adding entries and checking if processed."""
        ledger = PaperLedger(ledger_path=temp_ledger_path)

        paper_dict = {
            "canonical_id": "arxiv:2401.12345",
            "source": "arxiv",
            "arxiv_id": "2401.12345",
            "doi": None,
            "title": "Test Paper",
            "authors": "Author One; Author Two",
            "venue": "arXiv",
            "year": 2024,
            "url": "https://arxiv.org/pdf/2401.12345.pdf",
        }

        # Initially not processed
        assert not ledger.is_processed("arxiv:2401.12345")

        # Add entry
        ledger.add_entry(
            paper_dict=paper_dict,
            model_name="test-model",
            abstract_rewrite="Rewritten abstract",
            problem_solved="Problem statement",
            linkedin_post="LinkedIn post",
        )

        # Now it's processed
        assert ledger.is_processed("arxiv:2401.12345")
        assert len(ledger.ledger_rows) == 1

    def test_save_and_load(self, temp_ledger_path):
        """Test saving and loading ledger."""
        # Create and populate ledger
        ledger1 = PaperLedger(ledger_path=temp_ledger_path)

        paper_dict = {
            "canonical_id": "arxiv:2401.12345",
            "source": "arxiv",
            "arxiv_id": "2401.12345",
            "doi": None,
            "title": "Test Paper",
            "authors": "Author One",
            "venue": "arXiv",
            "year": 2024,
            "url": "https://arxiv.org/pdf/2401.12345.pdf",
        }

        ledger1.add_entry(
            paper_dict=paper_dict,
            model_name="test-model",
            abstract_rewrite="Rewritten",
            problem_solved="Problem",
            linkedin_post="Post",
        )

        # Save
        ledger1.save()
        assert temp_ledger_path.exists()

        # Load in new instance
        ledger2 = PaperLedger(ledger_path=temp_ledger_path)
        assert ledger2.is_processed("arxiv:2401.12345")
        assert len(ledger2.ledger_rows) == 1
        assert ledger2.ledger_rows[0]["title"] == "Test Paper"

    def test_multiple_entries(self, temp_ledger_path):
        """Test adding multiple entries."""
        ledger = PaperLedger(ledger_path=temp_ledger_path)

        for i in range(5):
            paper_dict = {
                "canonical_id": f"arxiv:2401.1234{i}",
                "source": "arxiv",
                "arxiv_id": f"2401.1234{i}",
                "doi": None,
                "title": f"Paper {i}",
                "authors": "Author",
                "venue": "arXiv",
                "year": 2024,
                "url": f"https://arxiv.org/pdf/2401.1234{i}.pdf",
            }

            ledger.add_entry(
                paper_dict=paper_dict,
                model_name="test",
                abstract_rewrite="Abstract",
                problem_solved="Problem",
                linkedin_post="Post",
            )

        assert len(ledger.processed_ids) == 5
        assert len(ledger.ledger_rows) == 5

        # Check all are marked as processed
        for i in range(5):
            assert ledger.is_processed(f"arxiv:2401.1234{i}")

    def test_duplicate_prevention(self, temp_ledger_path):
        """Test that duplicate IDs are tracked."""
        ledger = PaperLedger(ledger_path=temp_ledger_path)

        paper_dict = {
            "canonical_id": "arxiv:2401.12345",
            "source": "arxiv",
            "arxiv_id": "2401.12345",
            "doi": None,
            "title": "Test Paper",
            "authors": "Author",
            "venue": "arXiv",
            "year": 2024,
            "url": "https://arxiv.org/pdf/2401.12345.pdf",
        }

        ledger.add_entry(
            paper_dict=paper_dict,
            model_name="test",
            abstract_rewrite="A",
            problem_solved="B",
            linkedin_post="C",
        )

        # Check before adding duplicate
        assert ledger.is_processed("arxiv:2401.12345")

        # In real usage, the pipeline would skip this
        # But ledger itself doesn't prevent adding duplicates to rows
        # It only tracks what's processed
        assert len(ledger.ledger_rows) == 1
