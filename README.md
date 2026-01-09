# Twitter/X Scraper

A Python toolkit for extracting metadata from Twitter/X tweets, with support for multiple scraping methods and specialized Claude Code agents.

## Features

- **Tweet Metadata Extraction**: Extract comprehensive metadata from any tweet URL or ID
- **Multiple Methods**: Supports Twitter Syndication API (no auth) and twscrape (with accounts)
- **Async Support**: Built with asyncio for efficient concurrent operations
- **Export Formats**: JSON output with structured metadata
- **Claude Code Agents**: 8 specialized agents for different scraping tasks

## Installation

```bash
# Clone the repository
git clone https://github.com/VincenzoImp/twitter-scraper.git
cd twitter-scraper

# Create virtual environment (Python 3.10+ required)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install httpx twscrape
```

## Quick Start

### Extract Tweet Metadata

```bash
# Using tweet URL
python get_tweet_metadata.py "https://x.com/elonmusk/status/1349129669258448897"

# Using tweet ID directly
python get_tweet_metadata.py "1349129669258448897"

# Include raw API response data
python get_tweet_metadata.py "https://x.com/user/status/123" --raw
```

### Output Example

```
============================================================
TWEET METADATA
(source: syndication_api)
============================================================

 IDENTIFIERS
   ID: 1349129669258448897
   URL: https://x.com/elonmusk/status/1349129669258448897

 AUTHOR
   Username: @elonmusk
   Name: Elon Musk
   Verified: Yes

 CONTENT
   Text: Hey you... Yeah you Queen... You're gonna make it!
   Language: en
   Date: 2021-01-12T23:02:33.000Z

 ENGAGEMENT
   Likes: 519,046

============================================================

Metadata saved to: tweet_1349129669258448897_metadata.json
```

## Extracted Metadata

| Category | Fields |
|----------|--------|
| **Identifiers** | tweet_id, tweet_url, source_method |
| **Author** | id, username, display_name, verified, followers, following, tweet_count, bio, profile_image |
| **Content** | text, language, source, created_at |
| **Engagement** | like_count, retweet_count, reply_count, quote_count, view_count, bookmark_count |
| **Media** | has_media, media_count, media_urls, media_types |
| **Context** | is_retweet, is_quote, is_reply, reply_to_user, conversation_id |
| **Entities** | hashtags, mentions, urls |

## Scraping Methods

### 1. Twitter Syndication API (Default)

- **Pros**: No authentication required, simple setup
- **Cons**: Limited to certain tweets, less data available
- **Best for**: Quick lookups, public viral tweets

### 2. twscrape (Optional)

- **Pros**: Full data access, supports search/timeline
- **Cons**: Requires authenticated X accounts
- **Best for**: Large-scale scraping, complete data needs

```bash
# Setup twscrape accounts
twscrape add_accounts accounts.txt  # format: user:pass:email:email_pass
twscrape login_accounts

# Use twscrape method
python get_tweet_metadata.py "https://x.com/user/status/123" --twscrape
```

## Claude Code Agents

This project includes 8 specialized agents in `.claude/agents/`:

| Agent | Description |
|-------|-------------|
| `twitter-scraper` | Core scraping with twscrape and Syndication API |
| `data-pipeline` | ETL workflows, batch processing, database schemas |
| `data-analyzer` | Engagement analysis, trends, metrics calculation |
| `rate-limit-manager` | Token bucket, exponential backoff, circuit breaker |
| `search-specialist` | Advanced Twitter search queries and operators |
| `account-manager` | twscrape account pool configuration and monitoring |
| `media-downloader` | High-quality image/video download from tweets |
| `json-exporter` | Export to JSON, CSV, SQLite, Parquet, Excel |

### Using Agents in Claude Code

```
/agents
```

Then select the agent you need, or ask Claude to use a specific agent for your task.

## Project Structure

```
twitter-scraper/
├── get_tweet_metadata.py    # Main script
├── README.md                # This file
├── CLAUDE.md               # Claude Code instructions
├── .claude/
│   └── agents/             # Specialized agents
│       ├── twitter-scraper.md
│       ├── data-pipeline.md
│       ├── data-analyzer.md
│       ├── rate-limit-manager.md
│       ├── search-specialist.md
│       ├── account-manager.md
│       ├── media-downloader.md
│       └── json-exporter.md
└── venv/                   # Virtual environment (not tracked)
```

## API Limitations

### Twitter Syndication API
- Works only for certain public tweets
- No search or timeline access
- Rate limits apply

### twscrape
- Requires authenticated X accounts
- Rate limit: ~300 requests/hour per IP
- Timeline limited to ~3200 tweets
- Accounts may get locked/suspended

## Legal Notice

This tool is for educational and research purposes. Scraping Twitter/X:
- May violate Twitter's Terms of Service
- Should be done responsibly with rate limiting
- Should respect user privacy
- May result in account/IP bans

Always consult legal counsel for commercial use.

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.

## Resources

- [twscrape Documentation](https://github.com/vladkens/twscrape)
- [Twitter API Documentation](https://developer.twitter.com/en/docs)
- [Claude Code](https://claude.ai/claude-code)
