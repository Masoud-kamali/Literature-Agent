"""arXiv API client for fetching Gaussian Splatting papers."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode

import feedparser
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class ArxivPaper:
    """Represents a paper from arXiv."""

    def __init__(
        self,
        arxiv_id: str,
        title: str,
        authors: List[str],
        abstract: str,
        published: datetime,
        updated: datetime,
        primary_category: str,
        pdf_url: str,
        categories: List[str],
    ):
        self.arxiv_id = arxiv_id
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.published = published
        self.updated = updated
        self.primary_category = primary_category
        self.pdf_url = pdf_url
        self.categories = categories
        self.source = "arxiv"
        self.venue = "arXiv"
        self.year = published.year

    def to_dict(self) -> dict:
        """Convert to dictionary for ledger storage."""
        return {
            "canonical_id": self.arxiv_id,
            "source": self.source,
            "arxiv_id": self.arxiv_id,
            "doi": None,
            "title": self.title,
            "authors": "; ".join(self.authors),
            "venue": self.venue,
            "year": self.year,
            "url": self.pdf_url,
            "abstract": self.abstract,
            "primary_category": self.primary_category,
            "categories": "; ".join(self.categories),
        }


class ArxivClient:
    """Client for arXiv API with retry logic and rate limiting."""

    def __init__(self):
        self.base_url = settings.arxiv_base_url
        self.delay = settings.arxiv_delay

    @retry(
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(multiplier=settings.http_retry_delay, max=60),
    )
    async def _fetch_with_retry(self, url: str) -> str:
        """Fetch URL with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/atom+xml",
        }
        async with httpx.AsyncClient(timeout=settings.http_timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _parse_entry(self, entry) -> ArxivPaper:
        """Parse a single arXiv feed entry."""
        # Extract arXiv ID from the id field
        arxiv_id = entry.id.split("/abs/")[-1]

        # Parse authors
        authors = [author.name for author in entry.get("authors", [])]

        # Parse dates
        published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
        updated = datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%SZ")

        # Extract categories
        primary_category = entry.get("arxiv_primary_category", {}).get("term", "cs.CV")
        categories = [tag.term for tag in entry.get("tags", [])]

        # PDF link
        pdf_url = entry.id.replace("/abs/", "/pdf/") + ".pdf"

        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=entry.title.replace("\n", " ").strip(),
            authors=authors,
            abstract=entry.summary.replace("\n", " ").strip(),
            published=published,
            updated=updated,
            primary_category=primary_category,
            pdf_url=pdf_url,
            categories=categories,
        )

    async def search_papers(
        self,
        keywords: Optional[List[str]] = None,
        days_back: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> List[ArxivPaper]:
        """
        Search arXiv for papers matching keywords within date range.

        Args:
            keywords: List of search terms (defaults to config keywords)
            days_back: Number of days to look back (defaults to config)
            max_results: Maximum results to return (defaults to config)

        Returns:
            List of ArxivPaper objects
        """
        keywords = keywords or settings.search_keywords
        days_back = days_back or settings.default_days_back
        max_results = max_results or settings.max_results_per_source

        # Build search query with OR logic for keywords
        keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])
        search_query = f"all:{keyword_query}"

        # Date filter (arXiv uses submittedDate)
        start_date = datetime.now() - timedelta(days=days_back)
        date_filter = start_date.strftime("%Y%m%d%H%M%S")

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{self.base_url}?{urlencode(params)}"
        logger.info(f"Fetching arXiv papers: {search_query} (last {days_back} days)")

        try:
            # Fetch feed
            content = await self._fetch_with_retry(url)

            # Parse with feedparser
            feed = feedparser.parse(content)

            papers = []
            for entry in feed.entries:
                try:
                    paper = self._parse_entry(entry)

                    # Filter by date (submitted or updated within range)
                    if paper.published >= start_date or paper.updated >= start_date:
                        papers.append(paper)
                        logger.debug(f"Found arXiv paper: {paper.arxiv_id} - {paper.title}")
                except Exception as e:
                    logger.warning(f"Failed to parse arXiv entry: {e}")
                    continue

            logger.info(f"Retrieved {len(papers)} papers from arXiv")

            # Rate limiting
            await asyncio.sleep(self.delay)

            return papers

        except Exception as e:
            logger.error(f"Failed to fetch arXiv papers: {e}")
            return []
