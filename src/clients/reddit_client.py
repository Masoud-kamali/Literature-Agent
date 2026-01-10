"""Reddit client for fetching relevant posts from specific subreddits."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class RedditPost:
    """Represents a post from Reddit."""

    def __init__(
        self,
        post_id: str,
        title: str,
        author: str,
        subreddit: str,
        selftext: str,
        url: str,
        permalink: str,
        created_utc: datetime,
        score: int,
        num_comments: int,
    ):
        self.post_id = post_id
        self.title = title
        self.author = author
        self.subreddit = subreddit
        self.selftext = selftext
        self.url = url
        self.permalink = permalink
        self.created_utc = created_utc
        self.score = score
        self.num_comments = num_comments
        self.source = "reddit"
        self.year = created_utc.year

    def to_dict(self) -> dict:
        """Convert to dictionary for ledger storage."""
        return {
            "canonical_id": f"reddit_{self.post_id}",
            "source": self.source,
            "post_id": self.post_id,
            "title": self.title,
            "authors": f"u/{self.author}",
            "venue": f"r/{self.subreddit}",
            "year": self.year,
            "url": f"https://reddit.com{self.permalink}",
            "abstract": self.selftext or self.title,
            "subreddit": self.subreddit,
            "score": self.score,
            "num_comments": self.num_comments,
            "external_url": self.url if self.url != f"https://reddit.com{self.permalink}" else None,
        }


class RedditClient:
    """Client for Reddit JSON API (no authentication required for public posts)."""

    def __init__(self):
        self.base_url = settings.reddit_base_url
        self.delay = settings.reddit_delay
        self.user_agent = settings.reddit_user_agent

    @retry(
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(multiplier=settings.http_retry_delay, max=60),
    )
    async def _fetch_with_retry(self, url: str) -> dict:
        """Fetch URL with retry logic."""
        headers = {
            "User-Agent": self.user_agent,
        }
        async with httpx.AsyncClient(timeout=settings.http_timeout, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def _parse_post(self, post_data: dict) -> Optional[RedditPost]:
        """Parse a single Reddit post."""
        try:
            data = post_data.get("data", {})

            post_id = data.get("id")
            title = data.get("title", "").strip()
            author = data.get("author", "")
            subreddit = data.get("subreddit", "")
            selftext = data.get("selftext", "").strip()
            url = data.get("url", "")
            permalink = data.get("permalink", "")
            created_utc = datetime.fromtimestamp(data.get("created_utc", 0))
            score = data.get("score", 0)
            num_comments = data.get("num_comments", 0)

            # Skip deleted/removed posts
            if author in ["[deleted]", "[removed]"]:
                return None

            return RedditPost(
                post_id=post_id,
                title=title,
                author=author,
                subreddit=subreddit,
                selftext=selftext,
                url=url,
                permalink=permalink,
                created_utc=created_utc,
                score=score,
                num_comments=num_comments,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Reddit post: {e}")
            return None

    async def search_subreddit(
        self,
        subreddit: str,
        days_back: Optional[int] = None,
        max_results: Optional[int] = None,
        keywords: Optional[List[str]] = None,
    ) -> List[RedditPost]:
        """
        Search a specific subreddit for posts within date range.

        Args:
            subreddit: Subreddit name (without r/ prefix)
            days_back: Number of days to look back (defaults to config)
            max_results: Maximum results to return (defaults to config)
            keywords: Optional keywords to filter posts

        Returns:
            List of RedditPost objects
        """
        days_back = days_back or settings.default_days_back
        max_results = max_results or settings.max_results_per_source

        # Use Reddit JSON API (no auth required for public posts)
        url = f"{self.base_url}/r/{subreddit}/new.json?limit={min(max_results, 100)}"

        logger.info(f"Fetching Reddit posts from r/{subreddit} (last {days_back} days)")

        try:
            data = await self._fetch_with_retry(url)

            posts = []
            start_date = datetime.now() - timedelta(days=days_back)

            children = data.get("data", {}).get("children", [])

            for child in children:
                post = self._parse_post(child)

                if post and post.created_utc >= start_date:
                    # Filter by keywords if provided
                    if keywords:
                        text_to_search = (post.title + " " + post.selftext).lower()
                        if any(kw.lower() in text_to_search for kw in keywords):
                            posts.append(post)
                            logger.debug(f"Found Reddit post: {post.post_id} - {post.title}")
                    else:
                        posts.append(post)
                        logger.debug(f"Found Reddit post: {post.post_id} - {post.title}")

            logger.info(f"Retrieved {len(posts)} posts from r/{subreddit}")

            # Rate limiting
            await asyncio.sleep(self.delay)

            return posts

        except Exception as e:
            logger.error(f"Failed to fetch Reddit posts from r/{subreddit}: {e}")
            return []

    async def search_all_subreddits(
        self,
        subreddits: Optional[List[str]] = None,
        days_back: Optional[int] = None,
        max_results: Optional[int] = None,
        keywords: Optional[List[str]] = None,
    ) -> List[RedditPost]:
        """
        Search multiple subreddits concurrently.

        Args:
            subreddits: List of subreddit names (defaults to config)
            days_back: Number of days to look back
            max_results: Maximum results per subreddit
            keywords: Optional keywords to filter posts

        Returns:
            Combined list of RedditPost objects
        """
        subreddits = subreddits or settings.reddit_subreddits

        logger.info(f"Searching {len(subreddits)} subreddits")

        # Search all subreddits concurrently
        tasks = [
            self.search_subreddit(
                subreddit=sub,
                days_back=days_back,
                max_results=max_results,
                keywords=keywords,
            )
            for sub in subreddits
        ]

        results = await asyncio.gather(*tasks)

        # Flatten and sort by score (most popular first)
        all_posts = []
        for posts in results:
            all_posts.extend(posts)

        all_posts.sort(key=lambda p: p.score, reverse=True)

        logger.info(f"Retrieved total of {len(all_posts)} posts from all subreddits")

        return all_posts

