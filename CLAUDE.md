# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Twitter/X scraper toolkit for extracting tweet metadata. Uses Python 3.10+ with async support.

## Key Files

- `get_tweet_metadata.py` - Main script for extracting tweet metadata
- `.claude/agents/` - 8 specialized agents for different tasks

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install httpx twscrape

# Run
python get_tweet_metadata.py <tweet_url_or_id>
python get_tweet_metadata.py "https://x.com/user/status/123"
python get_tweet_metadata.py "123456789" --raw
python get_tweet_metadata.py "https://x.com/user/status/123" --twscrape

# twscrape account management
twscrape add_accounts accounts.txt
twscrape login_accounts
twscrape accounts
```

## Architecture

### Scraping Methods

1. **Syndication API** (default): Public endpoint at `cdn.syndication.twimg.com`, no auth needed but limited
2. **twscrape**: Full-featured, requires authenticated X accounts in pool

### Data Flow

```
Tweet URL/ID → extract_tweet_id() → get_tweet_via_syndication() or get_tweet_with_twscrape() → TweetMetadata → JSON output
```

### TweetMetadata Structure

```python
@dataclass
class TweetMetadata:
    # Identifiers
    tweet_id: str
    tweet_url: str
    source_method: str

    # Author info
    author_id, author_username, author_display_name
    author_verified, author_followers_count, etc.

    # Content
    text, language, source, created_at

    # Engagement
    like_count, retweet_count, reply_count, quote_count, view_count

    # Media
    has_media, media_count, media_urls, media_types

    # Context
    is_retweet, is_quote, is_reply, conversation_id

    # Entities
    hashtags, mentions, urls
```

## Agents

Use the appropriate agent for specific tasks:

| Task | Agent |
|------|-------|
| Basic scraping | `twitter-scraper` |
| Build data pipelines | `data-pipeline` |
| Analyze engagement | `data-analyzer` |
| Handle rate limits | `rate-limit-manager` |
| Build search queries | `search-specialist` |
| Manage accounts | `account-manager` |
| Download media | `media-downloader` |
| Export data | `json-exporter` |

## Code Style

- Python 3.10+ with type hints
- Async/await for I/O operations
- Dataclasses for structured data
- httpx for HTTP requests
- Error messages to stdout (no logging framework)

## Common Tasks

### Add new metadata field

1. Add field to `TweetMetadata` dataclass
2. Extract from API response in `get_tweet_via_syndication()` and/or `get_tweet_with_twscrape()`
3. Add to `print_metadata()` output

### Support new tweet URL format

Add regex pattern to `extract_tweet_id()` function.

### Add new export format

See `json-exporter` agent for patterns. Implement in separate module.

## Testing

```bash
# Test with known working tweet
python get_tweet_metadata.py "20"  # Jack Dorsey's first tweet

# Test syndication API directly
curl "https://cdn.syndication.twimg.com/tweet-result?id=20&token=0"
```

## Limitations

- Syndication API only works for some tweets (older/popular ones)
- twscrape requires maintaining authenticated accounts
- Rate limits: ~300 req/hour per IP
- No streaming/real-time support yet
