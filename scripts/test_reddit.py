#!/usr/bin/env python3
"""Test script for Reddit client functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.clients.reddit_client import RedditClient
from src.config import settings


async def main():
    """Test Reddit client."""
    logger.info("=" * 80)
    logger.info("Testing Reddit Client")
    logger.info("=" * 80)

    client = RedditClient()

    # Test 1: Search a single subreddit
    logger.info("\n--- Test 1: Search r/GaussianSplatting ---")
    posts = await client.search_subreddit(
        subreddit="GaussianSplatting",
        days_back=30,
        max_results=5,
        keywords=settings.search_keywords,
    )

    logger.info(f"Found {len(posts)} posts in r/GaussianSplatting")
    for i, post in enumerate(posts[:3], 1):
        logger.info(f"\nPost {i}:")
        logger.info(f"  Title: {post.title}")
        logger.info(f"  Author: u/{post.author}")
        logger.info(f"  Score: {post.score}")
        logger.info(f"  URL: https://reddit.com{post.permalink}")

    # Test 2: Search all configured subreddits
    logger.info("\n--- Test 2: Search all subreddits ---")
    all_posts = await client.search_all_subreddits(
        days_back=30,
        max_results=5,
        keywords=settings.search_keywords,
    )

    logger.info(f"Found {len(all_posts)} posts across all subreddits")
    for i, post in enumerate(all_posts[:3], 1):
        logger.info(f"\nPost {i}:")
        logger.info(f"  Subreddit: r/{post.subreddit}")
        logger.info(f"  Title: {post.title}")
        logger.info(f"  Score: {post.score}")

    # Test 3: Check data dictionary format
    if all_posts:
        logger.info("\n--- Test 3: Data dictionary format ---")
        sample_dict = all_posts[0].to_dict()
        logger.info("Sample post dictionary:")
        for key, value in sample_dict.items():
            logger.info(f"  {key}: {value}")

    logger.info("\n" + "=" * 80)
    logger.info("Reddit Client Test Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

