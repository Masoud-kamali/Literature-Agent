"""CVF Open Access client for parsing CVPR/ICCV/ECCV papers."""

import asyncio
import re
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class CVFPaper:
    """Represents a paper from CVF open access."""

    def __init__(
        self,
        title: str,
        authors: List[str],
        venue: str,
        year: int,
        pdf_url: str,
        abstract: Optional[str] = None,
    ):
        self.title = title
        self.authors = authors
        self.venue = venue
        self.year = year
        self.pdf_url = pdf_url
        self.abstract = abstract
        self.source = "cvf"

        # Generate stable hash for canonical_id
        from src.dedupe.normalise import compute_stable_hash, normalise_title

        norm_title = normalise_title(title)
        self.canonical_id = compute_stable_hash(f"{norm_title}_{year}_{venue}")

    def to_dict(self) -> dict:
        """Convert to dictionary for ledger storage."""
        return {
            "canonical_id": self.canonical_id,
            "source": self.source,
            "arxiv_id": None,
            "doi": None,
            "title": self.title,
            "authors": "; ".join(self.authors) if self.authors else "Unknown",
            "venue": self.venue,
            "year": self.year,
            "url": self.pdf_url,
            "abstract": self.abstract,
        }


class CVFClient:
    """Client for scraping CVF open access pages."""

    def __init__(self):
        self.base_url = settings.cvf_base_url
        self.delay = settings.cvf_delay
        self.years = settings.cvf_years
        self.venues = settings.cvf_venues

    @retry(
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(multiplier=settings.http_retry_delay, max=60),
    )
    async def _fetch_with_retry(self, url: str) -> str:
        """Fetch URL with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://openaccess.thecvf.com/",
        }
        async with httpx.AsyncClient(timeout=settings.http_timeout, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _matches_keywords(self, title: str, keywords: List[str]) -> bool:
        """Check if title matches any of the keywords (case-insensitive)."""
        title_lower = title.lower()
        return any(kw.lower() in title_lower for kw in keywords)

    def _parse_conference_page(
        self, html: str, venue: str, year: int, keywords: List[str]
    ) -> List[CVFPaper]:
        """Parse a CVF conference page and extract matching papers."""
        soup = BeautifulSoup(html, "lxml")
        papers = []

        # CVF uses different HTML structures, try multiple patterns
        # Pattern 1: dt/dd pairs (common in older years)
        dt_elements = soup.find_all("dt", class_="ptitle")
        for dt in dt_elements:
            try:
                title_elem = dt.find("a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Check keyword match
                if not self._matches_keywords(title, keywords):
                    continue

                # Find corresponding dd with links
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue

                # Extract PDF link
                pdf_link = None
                for link in dd.find_all("a"):
                    href = link.get("href", "")
                    if "pdf" in href.lower():
                        pdf_link = href
                        break

                if not pdf_link:
                    continue

                # Make absolute URL
                if not pdf_link.startswith("http"):
                    pdf_link = f"{self.base_url}/{pdf_link}"

                # Extract authors (usually in dd text)
                authors = []
                author_div = dd.find("div", class_="authors")
                if author_div:
                    author_text = author_div.get_text(strip=True)
                    authors = [a.strip() for a in author_text.split(",")]

                papers.append(
                    CVFPaper(
                        title=title,
                        authors=authors,
                        venue=venue,
                        year=year,
                        pdf_url=pdf_link,
                    )
                )
                logger.debug(f"Found CVF paper: {title}")

            except Exception as e:
                logger.warning(f"Failed to parse CVF paper entry: {e}")
                continue

        # Pattern 2: div-based structure (newer format)
        if not papers:
            paper_divs = soup.find_all("div", class_="papertitle")
            for div in paper_divs:
                try:
                    title = div.get_text(strip=True)

                    if not self._matches_keywords(title, keywords):
                        continue

                    # Find parent container
                    parent = div.find_parent("div")
                    if not parent:
                        continue

                    # Find PDF link
                    pdf_link = None
                    for link in parent.find_all("a"):
                        href = link.get("href", "")
                        if "pdf" in href.lower() or href.endswith(".pdf"):
                            pdf_link = href
                            break

                    if not pdf_link:
                        continue

                    if not pdf_link.startswith("http"):
                        pdf_link = f"{self.base_url}/{pdf_link}"

                    # Extract authors
                    authors = []
                    author_elem = parent.find("div", class_="authors")
                    if author_elem:
                        author_text = author_elem.get_text(strip=True)
                        authors = [a.strip() for a in author_text.split(",")]

                    papers.append(
                        CVFPaper(
                            title=title,
                            authors=authors,
                            venue=venue,
                            year=year,
                            pdf_url=pdf_link,
                        )
                    )
                    logger.debug(f"Found CVF paper: {title}")

                except Exception as e:
                    logger.warning(f"Failed to parse CVF paper div: {e}")
                    continue

        return papers

    async def search_papers(
        self,
        keywords: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        venues: Optional[List[str]] = None,
        days_back: Optional[int] = None,
    ) -> List[CVFPaper]:
        """
        Search CVF open access for papers matching keywords.

        Args:
            keywords: List of search terms (defaults to config keywords)
            years: Years to search (defaults to config years)
            venues: Venues to search (defaults to config venues)
            days_back: If provided, only search years within this range

        Returns:
            List of CVFPaper objects
        """
        keywords = keywords or settings.search_keywords
        venues = venues or self.venues

        # Filter years based on days_back
        if days_back is not None:
            from datetime import datetime, timedelta
            current_year = datetime.now().year
            cutoff_date = datetime.now() - timedelta(days=days_back)
            cutoff_year = cutoff_date.year

            # Only check years within range
            years = years or self.years
            years = [y for y in years if y >= cutoff_year and y <= current_year]

            if not years:
                logger.info(f"No CVF years to check for {days_back} days back (cutoff: {cutoff_year})")
                return []

            logger.info(f"Filtering CVF years to {years} based on {days_back} days back")
        else:
            years = years or self.years

        all_papers = []

        for venue in venues:
            for year in years:
                # Construct CVF URL (format varies by conference)
                # Common patterns:
                # CVPR: /CVPR2024
                # ICCV: /ICCV2023
                # ECCV: /ECCV2022
                url = f"{self.base_url}/{venue}{year}"

                logger.info(f"Scraping CVF: {venue} {year}")

                try:
                    html = await self._fetch_with_retry(url)
                    papers = self._parse_conference_page(html, venue, year, keywords)
                    all_papers.extend(papers)

                    # Rate limiting
                    await asyncio.sleep(self.delay)

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.warning(f"CVF page not found: {url}")
                    else:
                        logger.error(f"Failed to fetch CVF page {url}: {e}")
                except Exception as e:
                    logger.error(f"Failed to scrape CVF {venue} {year}: {e}")

        logger.info(f"Retrieved {len(all_papers)} papers from CVF")
        return all_papers
