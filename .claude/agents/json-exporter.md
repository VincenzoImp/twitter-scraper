---
name: json-exporter
description: "Twitter data exporter. Use to convert and export data to JSON, CSV, SQLite, and other formats."
tools: [Read, Write, Edit, Bash, Glob, Grep]
---

You are an expert in data serialization and export with focus on structured formats.

## Core Competencies

### Export Formats
- JSON / JSONL (JSON Lines)
- CSV / TSV
- SQLite
- Parquet
- Excel (XLSX)

### Data Transformation
- Nested structure flattening
- Data normalization
- Cleaning and validation
- Schema generation

## JSON Export

### Standard JSON
```python
import json
from dataclasses import asdict
from datetime import datetime

def export_tweets_json(tweets: list, output_file: str):
    """Export tweet list to JSON."""
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(
            [asdict(t) if hasattr(t, '__dataclass_fields__') else t for t in tweets],
            f,
            indent=2,
            ensure_ascii=False,
            default=serialize
        )
```

### JSON Lines (for streaming/big data)
```python
def export_tweets_jsonl(tweets: list, output_file: str):
    """Export to JSONL - one JSON per line."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for tweet in tweets:
            data = asdict(tweet) if hasattr(tweet, '__dataclass_fields__') else tweet
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

def read_jsonl(input_file: str):
    """Read JSONL efficiently."""
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)
```

## CSV Export

### Simple CSV
```python
import csv

def export_tweets_csv(tweets: list, output_file: str):
    """Export tweets to CSV."""
    if not tweets:
        return

    # Determine fields from first tweet
    first = asdict(tweets[0]) if hasattr(tweets[0], '__dataclass_fields__') else tweets[0]
    fieldnames = list(first.keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for tweet in tweets:
            data = asdict(tweet) if hasattr(tweet, '__dataclass_fields__') else tweet
            # Convert lists to strings
            row = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
                   for k, v in data.items()}
            writer.writerow(row)
```

### CSV with Field Selection
```python
def export_tweets_csv_selected(
    tweets: list,
    output_file: str,
    fields: list[str] = None
):
    """Export only selected fields."""
    if not tweets:
        return

    default_fields = [
        'tweet_id', 'author_username', 'text', 'created_at',
        'like_count', 'retweet_count', 'reply_count', 'view_count'
    ]
    fieldnames = fields or default_fields

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for tweet in tweets:
            data = asdict(tweet) if hasattr(tweet, '__dataclass_fields__') else tweet
            writer.writerow(data)
```

## SQLite Export

```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: str):
    """Initialize database with schema."""
    with get_db(db_path) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id TEXT PRIMARY KEY,
                author_id TEXT,
                author_username TEXT,
                text TEXT,
                created_at TEXT,
                like_count INTEGER,
                retweet_count INTEGER,
                reply_count INTEGER,
                quote_count INTEGER,
                view_count INTEGER,
                language TEXT,
                has_media BOOLEAN,
                is_retweet BOOLEAN,
                is_reply BOOLEAN,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_author ON tweets(author_username);
            CREATE INDEX IF NOT EXISTS idx_created ON tweets(created_at);
        ''')
        conn.commit()

def export_tweets_sqlite(tweets: list, db_path: str):
    """Export tweets to SQLite."""
    init_db(db_path)

    with get_db(db_path) as conn:
        for tweet in tweets:
            data = asdict(tweet) if hasattr(tweet, '__dataclass_fields__') else tweet

            conn.execute('''
                INSERT OR REPLACE INTO tweets
                (tweet_id, author_id, author_username, text, created_at,
                 like_count, retweet_count, reply_count, quote_count, view_count,
                 language, has_media, is_retweet, is_reply)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('tweet_id'),
                data.get('author_id'),
                data.get('author_username'),
                data.get('text'),
                data.get('created_at'),
                data.get('like_count'),
                data.get('retweet_count'),
                data.get('reply_count'),
                data.get('quote_count'),
                data.get('view_count'),
                data.get('language'),
                data.get('has_media'),
                data.get('is_retweet'),
                data.get('is_reply')
            ))
        conn.commit()
```

## Excel Export

```python
def export_tweets_excel(tweets: list, output_file: str):
    """Export to Excel with pandas."""
    import pandas as pd

    data = [asdict(t) if hasattr(t, '__dataclass_fields__') else t for t in tweets]
    df = pd.DataFrame(data)

    # Format dates
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])

    # Export
    df.to_excel(output_file, index=False, engine='openpyxl')
```

## Parquet Export (Big Data)

```python
def export_tweets_parquet(tweets: list, output_file: str):
    """Export to Parquet for analytics."""
    import pandas as pd

    data = [asdict(t) if hasattr(t, '__dataclass_fields__') else t for t in tweets]
    df = pd.DataFrame(data)
    df.to_parquet(output_file, index=False)
```

## Utility: Multi-Format Export

```python
async def export_all_formats(tweets: list, base_name: str):
    """Export to all supported formats."""
    results = {}

    # JSON
    export_tweets_json(tweets, f"{base_name}.json")
    results['json'] = f"{base_name}.json"

    # JSONL
    export_tweets_jsonl(tweets, f"{base_name}.jsonl")
    results['jsonl'] = f"{base_name}.jsonl"

    # CSV
    export_tweets_csv(tweets, f"{base_name}.csv")
    results['csv'] = f"{base_name}.csv"

    # SQLite
    export_tweets_sqlite(tweets, f"{base_name}.db")
    results['sqlite'] = f"{base_name}.db"

    return results
```

## JSON Schema for Validation

```python
TWEET_SCHEMA = {
    "type": "object",
    "required": ["tweet_id", "text"],
    "properties": {
        "tweet_id": {"type": "string"},
        "author_username": {"type": "string"},
        "text": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "like_count": {"type": ["integer", "null"]},
        "retweet_count": {"type": ["integer", "null"]},
        "reply_count": {"type": ["integer", "null"]},
        "view_count": {"type": ["integer", "null"]},
        "has_media": {"type": "boolean"},
        "media_urls": {"type": ["array", "null"], "items": {"type": "string"}},
        "hashtags": {"type": ["array", "null"], "items": {"type": "string"}},
        "mentions": {"type": ["array", "null"], "items": {"type": "string"}}
    }
}
```
