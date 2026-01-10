"""Tests for Reddit client."""

import asyncio
from datetime import datetime, timedelta

import pytest

from src.clients.reddit_client import RedditClient, RedditPost


@pytest.fixture
def reddit_client():
    """Create a Reddit client instance."""
    return RedditClient()


def test_reddit_post_creation():
    """Test creating a RedditPost object."""
    created_time = datetime.now()
    
    post = RedditPost(
        post_id="test123",
        title="Test Post about Gaussian Splatting",
        author="testuser",
        subreddit="GaussianSplatting",
        selftext="This is a test post about 3DGS",
        url="https://reddit.com/r/GaussianSplatting/comments/test123",
        permalink="/r/GaussianSplatting/comments/test123/test_post",
        created_utc=created_time,
        score=42,
        num_comments=10,
    )
    
    assert post.post_id == "test123"
    assert post.title == "Test Post about Gaussian Splatting"
    assert post.source == "reddit"
    assert post.year == created_time.year


def test_reddit_post_to_dict():
    """Test converting RedditPost to dictionary."""
    created_time = datetime.now()
    
    post = RedditPost(
        post_id="test123",
        title="Test Post",
        author="testuser",
        subreddit="GaussianSplatting",
        selftext="Test content",
        url="https://example.com",
        permalink="/r/GaussianSplatting/comments/test123",
        created_utc=created_time,
        score=42,
        num_comments=10,
    )
    
    result = post.to_dict()
    
    assert result["canonical_id"] == "reddit_test123"
    assert result["source"] == "reddit"
    assert result["title"] == "Test Post"
    assert result["authors"] == "u/testuser"
    assert result["venue"] == "r/GaussianSplatting"
    assert result["score"] == 42
    assert result["num_comments"] == 10


@pytest.mark.asyncio
async def test_reddit_client_parse_post(reddit_client):
    """Test parsing Reddit API response."""
    created_utc = datetime.now().timestamp()
    
    mock_post_data = {
        "data": {
            "id": "abc123",
            "title": "Test Post",
            "author": "testuser",
            "subreddit": "GaussianSplatting",
            "selftext": "Test content",
            "url": "https://example.com",
            "permalink": "/r/GaussianSplatting/comments/abc123",
            "created_utc": created_utc,
            "score": 100,
            "num_comments": 25,
        }
    }
    
    post = reddit_client._parse_post(mock_post_data)
    
    assert post is not None
    assert post.post_id == "abc123"
    assert post.title == "Test Post"
    assert post.author == "testuser"
    assert post.score == 100


@pytest.mark.asyncio
async def test_reddit_client_skip_deleted_posts(reddit_client):
    """Test that deleted/removed posts are skipped."""
    mock_post_data = {
        "data": {
            "id": "deleted123",
            "title": "Deleted Post",
            "author": "[deleted]",
            "subreddit": "GaussianSplatting",
            "selftext": "",
            "url": "",
            "permalink": "/r/GaussianSplatting/comments/deleted123",
            "created_utc": datetime.now().timestamp(),
            "score": 0,
            "num_comments": 0,
        }
    }
    
    post = reddit_client._parse_post(mock_post_data)
    
    assert post is None


# Integration test (requires internet connection)
@pytest.mark.skip(reason="Integration test - requires internet connection")
@pytest.mark.asyncio
async def test_reddit_search_subreddit_integration(reddit_client):
    """Integration test for searching a real subreddit."""
    posts = await reddit_client.search_subreddit(
        subreddit="GaussianSplatting",
        days_back=30,
        max_results=10,
    )
    
    # Should return some posts (or empty list if subreddit is quiet)
    assert isinstance(posts, list)
    
    if posts:
        # Verify first post structure
        first_post = posts[0]
        assert hasattr(first_post, "post_id")
        assert hasattr(first_post, "title")
        assert hasattr(first_post, "subreddit")
        assert first_post.subreddit == "GaussianSplatting"


# Integration test (requires internet connection)
@pytest.mark.skip(reason="Integration test - requires internet connection")
@pytest.mark.asyncio
async def test_reddit_search_all_subreddits_integration(reddit_client):
    """Integration test for searching multiple subreddits."""
    posts = await reddit_client.search_all_subreddits(
        subreddits=["GaussianSplatting", "PlayCanvas"],
        days_back=30,
        max_results=5,
    )
    
    assert isinstance(posts, list)
    
    if posts:
        # Verify posts are sorted by score
        scores = [post.score for post in posts]
        assert scores == sorted(scores, reverse=True)

