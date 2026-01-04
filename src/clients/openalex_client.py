"""OpenAlex API client for fetching academic papers."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class OpenAlexPaper:
    """Represents a paper from OpenAlex."""

    def __init__(
        self,
        openalex_id: str,
        title: str,
        authors: List[str],
        abstract: Optional[str],
        publication_date: datetime,
        doi: Optional[str],
        venue: Optional[str],
        pdf_url: Optional[str],
        landing_page_url: Optional[str],
    ):
        self.openalex_id = openalex_id
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.publication_date = publication_date
        self.doi = doi
        self.venue = venue or "Unknown"
        self.pdf_url = pdf_url
        self.landing_page_url = landing_page_url
        self.source = "openalex"
        self.year = publication_date.year if publication_date else None

    def to_dict(self) -> dict:
        """Convert to dictionary for ledger storage."""
        return {
            "canonical_id": self.doi or self.openalex_id,
            "source": self.source,
            "arxiv_id": None,
            "doi": self.doi,
            "title": self.title,
            "authors": "; ".join(self.authors),
            "venue": self.venue,
            "year": self.year,
            "url": self.pdf_url or self.landing_page_url,
            "abstract": self.abstract,
            "openalex_id": self.openalex_id,
        }


class OpenAlexClient:
    """Client for OpenAlex API with polite pool parameters."""

    def __init__(self):
        self.base_url = settings.openalex_base_url
        self.mailto = settings.openalex_mailto
        self.delay = settings.openalex_delay

    @retry(
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(multiplier=settings.http_retry_delay, max=60),
    )
    async def _fetch_with_retry(self, url: str, params: dict) -> dict:
        """Fetch URL with retry logic."""
        # Add polite pool parameter
        params["mailto"] = self.mailto

        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _parse_work(self, work: dict) -> Optional[OpenAlexPaper]:
        """Parse a single OpenAlex work."""
        try:
            # Extract basic info
            openalex_id = work.get("id", "").split("/")[-1]
            title = work.get("title", "").strip()

            if not title:
                return None

            # Authors
            authorships = work.get("authorships", [])
            authors = [
                a.get("author", {}).get("display_name", "Unknown")
                for a in authorships
                if a.get("author")
            ]

            # Abstract (inverted index format)
            abstract_inverted = work.get("abstract_inverted_index")
            abstract = None
            if abstract_inverted:
                # Reconstruct abstract from inverted index
                word_positions = []
                for word, positions in abstract_inverted.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([w for _, w in word_positions])

            # Publication date
            pub_date_str = work.get("publication_date")
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                except ValueError:
                    pass

            # DOI
            doi = work.get("doi", "").replace("https://doi.org/", "") if work.get("doi") else None

            # Venue
            venue_info = work.get("primary_location", {})
            venue = venue_info.get("source", {}).get("display_name") if venue_info else None

            # URLs
            pdf_url = None
            landing_page_url = work.get("doi") or None

            # Check for open access PDF
            open_access = work.get("open_access", {})
            if open_access.get("oa_url"):
                pdf_url = open_access["oa_url"]
            elif work.get("primary_location", {}).get("pdf_url"):
                pdf_url = work["primary_location"]["pdf_url"]

            return OpenAlexPaper(
                openalex_id=openalex_id,
                title=title,
                authors=authors,
                abstract=abstract,
                publication_date=pub_date,
                doi=doi,
                venue=venue,
                pdf_url=pdf_url,
                landing_page_url=landing_page_url,
            )

        except Exception as e:
            logger.warning(f"Failed to parse OpenAlex work: {e}")
            return None

    async def search_papers(
        self,
        keywords: Optional[List[str]] = None,
        days_back: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> List[OpenAlexPaper]:
        """
        Search OpenAlex for papers matching keywords within date range.

        Args:
            keywords: List of search terms (defaults to config keywords)
            days_back: Number of days to look back (defaults to config)
            max_results: Maximum results to return (defaults to config)

        Returns:
            List of OpenAlexPaper objects
        """
        keywords = keywords or settings.search_keywords
        days_back = days_back or settings.default_days_back
        max_results = max_results or settings.max_results_per_source

        # Build search query
        keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])

        # Date filter
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Build filter string
        filters = f"from_publication_date:{start_date}"

        params = {
            "search": keyword_query,
            "filter": filters,
            "per-page": min(max_results, 200),  # OpenAlex max is 200 per page
            "sort": "publication_date:desc",
        }

        url = f"{self.base_url}/works"
        logger.info(f"Fetching OpenAlex papers: {keyword_query} (from {start_date})")

        try:
            data = await self._fetch_with_retry(url, params)

            papers = []
            results = data.get("results", [])

            for work in results:
                paper = self._parse_work(work)
                if paper and paper.abstract:  # Only include papers with abstracts
                    papers.append(paper)
                    logger.debug(f"Found OpenAlex paper: {paper.openalex_id} - {paper.title}")

            logger.info(f"Retrieved {len(papers)} papers from OpenAlex")

            # Rate limiting
            await asyncio.sleep(self.delay)

            return papers

        except Exception as e:
            logger.error(f"Failed to fetch OpenAlex papers: {e}")
            return []
