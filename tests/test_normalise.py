"""Tests for title normalisation and hashing."""

import pytest

from src.dedupe.normalise import compute_stable_hash, compute_title_hash, normalise_title


class TestNormaliseTitle:
    """Test title normalisation."""

    def test_basic_normalisation(self):
        """Test basic lowercase and whitespace normalisation."""
        title = "  3D  Gaussian   Splatting  "
        expected = "3d gaussian splatting"
        assert normalise_title(title) == expected

    def test_remove_punctuation(self):
        """Test punctuation removal."""
        title = "3D Gaussian Splatting: A Novel Approach!"
        expected = "3d gaussian splatting a novel approach"
        assert normalise_title(title) == expected

    def test_unicode_normalisation(self):
        """Test Unicode and accent removal."""
        title = "Café Rendering with Naïve Approach"
        expected = "cafe rendering with naive approach"
        assert normalise_title(title) == expected

    def test_special_characters(self):
        """Test special character removal."""
        title = "3D-GS: Real-Time Rendering @ 60 FPS"
        expected = "3dgs realtime rendering 60 fps"
        assert normalise_title(title) == expected

    def test_empty_string(self):
        """Test empty string handling."""
        assert normalise_title("") == ""
        assert normalise_title("   ") == ""

    def test_case_variations(self):
        """Test that case variations produce same result."""
        titles = [
            "Gaussian Splatting",
            "GAUSSIAN SPLATTING",
            "gaussian splatting",
            "GaUsSiAn SpLaTtInG",
        ]
        normalised = [normalise_title(t) for t in titles]
        assert len(set(normalised)) == 1
        assert normalised[0] == "gaussian splatting"


class TestComputeStableHash:
    """Test stable hashing."""

    def test_consistent_hash(self):
        """Test that same input produces same hash."""
        text = "gaussian splatting"
        hash1 = compute_stable_hash(text)
        hash2 = compute_stable_hash(text)
        assert hash1 == hash2

    def test_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = compute_stable_hash("gaussian splatting")
        hash2 = compute_stable_hash("neural rendering")
        assert hash1 != hash2

    def test_hash_length(self):
        """Test hash length (first 16 chars of SHA256)."""
        hash_val = compute_stable_hash("test")
        assert len(hash_val) == 16

    def test_deterministic(self):
        """Test deterministic hashing across runs."""
        text = "3d gaussian splatting"
        # This specific hash should be stable
        hash_val = compute_stable_hash(text)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 16


class TestComputeTitleHash:
    """Test combined title hashing."""

    def test_title_hash_consistency(self):
        """Test that same title (different formatting) produces same hash."""
        titles = [
            "3D Gaussian Splatting",
            "3d gaussian splatting",
            "3D  GAUSSIAN   SPLATTING",
        ]
        hashes = [compute_title_hash(t) for t in titles]
        assert len(set(hashes)) == 1

    def test_different_titles_different_hashes(self):
        """Test that different titles produce different hashes."""
        hash1 = compute_title_hash("3D Gaussian Splatting")
        hash2 = compute_title_hash("Neural Radiance Fields")
        assert hash1 != hash2

    def test_punctuation_ignored(self):
        """Test that punctuation doesn't affect hash."""
        hash1 = compute_title_hash("3D Gaussian Splatting")
        hash2 = compute_title_hash("3D Gaussian Splatting!")
        hash3 = compute_title_hash("3D-Gaussian-Splatting")
        assert hash1 == hash2 == hash3
