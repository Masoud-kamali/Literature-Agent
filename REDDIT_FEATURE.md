# Reddit Integration Feature

## Overview

The literature-agent now includes Reddit integration to search for relevant tools, discussions, and community posts from specific subreddits. This allows you to create LinkedIn posts that combine **2 research papers + 1 tool/post** from the community.

## Configuration

### Subreddits to Monitor

By default, the agent monitors these subreddits:
- `r/PlayCanvas` - PlayCanvas engine discussions
- `r/GaussianSplatting` - 3D Gaussian Splatting community

You can customize this in your `.env` file or by modifying `src/config.py`:

```python
REDDIT_SUBREDDITS=["PlayCanvas", "GaussianSplatting", "YourCustomSubreddit"]
```

### Output Format

The output format is controlled by the `OUTPUT_FORMAT` setting:

- `2_papers_1_tool` (default): Generates posts with 2 research papers + 1 Reddit post/tool
- `3_papers`: Traditional format with 3 research papers only (no Reddit)

Set in `.env`:
```bash
OUTPUT_FORMAT=2_papers_1_tool
```

## How It Works

### 1. Reddit Data Collection

The `RedditClient` uses Reddit's public JSON API (no authentication required) to fetch recent posts:

```python
from src.clients.reddit_client import RedditClient

client = RedditClient()

# Search a single subreddit
posts = await client.search_subreddit(
    subreddit="GaussianSplatting",
    days_back=7,
    keywords=["gaussian splatting", "3DGS"]
)

# Search all configured subreddits
posts = await client.search_all_subreddits(
    days_back=7,
    max_results=20
)
```

### 2. Post Filtering

Reddit posts are filtered by:
- **Date range**: Only posts from the last N days (configurable)
- **Keywords**: Must match search keywords (e.g., "gaussian splatting", "3DGS")
- **Score**: Posts are sorted by score (upvotes - downvotes)
- **Deduplication**: Already processed posts are skipped using the ledger

### 3. Content Generation

For each Reddit post, the LLM generates:
- **Summary**: A concise description of the tool/discussion
- **Relevance**: Why it matters to the 3D Gaussian Splatting community
- **LinkedIn snippet**: Professional summary for social media

### 4. Output Format

The weekly report includes:

#### Papers Section
```markdown
## Paper 1: [Title]
**Authors**: [Authors]
**URL**: [URL]

### Technical Abstract
[Generated summary]

### Problem Addressed
[Generated problem statement]
```

#### Tools/Discussions Section
```markdown
## Tool/Discussion 1: [Post Title]
**Author**: u/username
**Subreddit**: r/SubredditName
**URL**: [Reddit URL]

### Summary
[Generated summary]

### Relevance
[Why it matters]
```

#### Combined LinkedIn Post
```
🔍 What's New in 3D Gaussian Splatting: Recent Ideas, Methods, and Applications

🧩 [Paper 1 Title]
👥 Authors: [Authors]
🔗 PDF: [URL]
💡 Core Idea: [Summary]
🎯 Why It Matters: [Impact]

🧩 [Paper 2 Title]
...

🛠️ [Reddit Post Title]
👤 By: u/username on r/Subreddit
🔗 Link: [URL]
📌 What It Is: [Summary]
🔗 Why It's Relevant: [Relevance]

#ComputerVision #3DGaussianSplatting #GenAI #Research
```

## Usage

### Basic Run

Process papers and Reddit posts from the last 7 days:

```bash
poetry run python scripts/run_weekly.py
```

This will:
1. Fetch 2 new research papers
2. Fetch 1 relevant Reddit post
3. Generate summaries for all items
4. Create a combined LinkedIn post

### Custom Lookback Period

Search the last 14 days:

```bash
poetry run python scripts/run_weekly.py --days 14
```

### Change Output Format

To get 3 papers without Reddit posts, set in `.env`:

```bash
OUTPUT_FORMAT=3_papers
```

Or modify `src/config.py` to change the default.

## Technical Details

### Reddit API

The integration uses Reddit's public JSON API:
- **Endpoint**: `https://www.reddit.com/r/{subreddit}/new.json`
- **Authentication**: Not required (public posts only)
- **Rate Limiting**: 2-second delay between requests (configurable)
- **User-Agent**: Custom user agent for polite API usage

### Data Model

Each Reddit post is stored with:

```python
{
    "canonical_id": "reddit_{post_id}",
    "source": "reddit",
    "post_id": "abc123",
    "title": "Post title",
    "authors": "u/username",
    "venue": "r/SubredditName",
    "year": 2026,
    "url": "https://reddit.com/r/...",
    "abstract": "Post content",
    "score": 42,
    "num_comments": 15,
    "external_url": "https://..."  # If post links to external content
}
```

### Deduplication

Reddit posts are deduplicated using the same ledger system as papers:
- **Canonical ID**: `reddit_{post_id}`
- **Storage**: `data/ledger.csv`
- **Persistence**: Once processed, posts are never processed again

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `REDDIT_BASE_URL` | `https://www.reddit.com` | Reddit base URL |
| `REDDIT_SUBREDDITS` | `["PlayCanvas", "GaussianSplatting"]` | Subreddits to monitor |
| `REDDIT_USER_AGENT` | `Literature-Agent/1.0` | User agent for API |
| `REDDIT_DELAY` | `2.0` | Seconds between requests |
| `OUTPUT_FORMAT` | `2_papers_1_tool` | Output format |

## Examples

### Example 1: Weekly Run with Reddit

```bash
poetry run python scripts/run_weekly.py --days 7
```

Output:
```
2026-01-10 10:00:00 | INFO | Starting Literature Agent Pipeline
2026-01-10 10:00:05 | INFO | Retrieved 45 papers from arXiv
2026-01-10 10:00:08 | INFO | Retrieved 23 papers from OpenAlex
2026-01-10 10:00:12 | INFO | Filtered to 2 new papers
2026-01-10 10:00:15 | INFO | Retrieved 12 Reddit posts
2026-01-10 10:00:16 | INFO | Filtered to 1 new Reddit post
2026-01-10 10:01:30 | INFO | Processing complete: 2 papers, 1 Reddit post
2026-01-10 10:01:31 | INFO | Outputs written to: output/week_2026_01_10
```

### Example 2: Papers Only (No Reddit)

Set `OUTPUT_FORMAT=3_papers` in `.env`, then:

```bash
poetry run python scripts/run_weekly.py
```

This will fetch 3 papers and skip Reddit entirely.

## Troubleshooting

### No Reddit Posts Found

**Problem**: Agent reports 0 Reddit posts

**Solutions**:
- Verify subreddit names are correct (case-sensitive)
- Increase lookback period: `--days 30`
- Check if keywords match post content
- Verify internet connectivity

### Reddit API Rate Limiting

**Problem**: HTTP 429 errors

**Solutions**:
- Increase `REDDIT_DELAY` in config (try 5.0 seconds)
- Reduce `MAX_RESULTS_PER_SOURCE`
- Check Reddit API status

### Posts Not Relevant

**Problem**: Reddit posts don't match research topic

**Solutions**:
- Adjust `SEARCH_KEYWORDS` in `src/config.py`
- Modify subreddit list to more focused communities
- Use keyword filtering more strictly

## Future Enhancements

Potential improvements:
1. **Reddit Comments**: Extract top comments for context
2. **GitHub Integration**: Fetch tool releases and repositories
3. **Discord/Slack**: Monitor community channels
4. **Custom Scoring**: Weight posts by engagement metrics
5. **Thread Analysis**: Analyze full discussion threads

## Contributing

To add more social/community sources:

1. Create a new client in `src/clients/` (e.g., `github_client.py`)
2. Follow the pattern from `reddit_client.py`
3. Add configuration in `src/config.py`
4. Integrate into `src/agents/pipeline.py`
5. Update output writer for new content type

## License

Apache License 2.0 - see [LICENSE](LICENSE) file.

