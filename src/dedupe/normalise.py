"""Title normalisation and stable hashing for deduplication."""

import hashlib
import re
import unicodedata


def normalise_title(title: str) -> str:
    """
    Normalise a paper title for deduplication.

    Steps:
    1. Convert to NFD Unicode normalisation
    2. Remove accents/diacritics
    3. Convert to lowercase
    4. Remove all non-alphanumeric characters except spaces
    5. Collapse multiple spaces to single space
    6. Strip leading/trailing whitespace

    Args:
        title: Raw paper title

    Returns:
        Normalised title string
    """
    if not title:
        return ""

    # NFD normalisation and accent removal
    title = unicodedata.normalize("NFD", title)
    title = "".join(char for char in title if unicodedata.category(char) != "Mn")

    # Lowercase
    title = title.lower()

    # Remove non-alphanumeric (keep spaces)
    title = re.sub(r"[^a-z0-9\s]", "", title)

    # Collapse whitespace
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def compute_stable_hash(text: str) -> str:
    """
    Compute a stable SHA256 hash of text.

    Args:
        text: Input text to hash

    Returns:
        Hexadecimal hash string (first 16 characters for brevity)
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def compute_title_hash(title: str) -> str:
    """
    Compute a stable hash from a normalised title.

    Args:
        title: Raw paper title

    Returns:
        Hash string suitable for deduplication
    """
    normalised = normalise_title(title)
    return compute_stable_hash(normalised)
