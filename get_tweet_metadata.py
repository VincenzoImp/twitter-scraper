#!/usr/bin/env python3
"""
Script to extract metadata from a Twitter/X tweet.

Available methods:
1. Twitter Syndication API (public, limited but works without auth)
2. twscrape (requires authenticated X accounts, complete data)

Usage:
    python get_tweet_metadata.py <tweet_url>
    python get_tweet_metadata.py https://x.com/elonmusk/status/1234567890

Requirements:
    pip install httpx
    pip install twscrape  # optional, for complete data
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, Any

import httpx

# Try to import twscrape (optional)
try:
    from twscrape import API, gather
    TWSCRAPE_AVAILABLE = True
except ImportError:
    TWSCRAPE_AVAILABLE = False


@dataclass
class TweetMetadata:
    """Data structure for tweet metadata."""
    # Identifiers
    tweet_id: str
    tweet_url: str
    source_method: str = "unknown"

    # Author
    author_id: Optional[str] = None
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    author_verified: Optional[bool] = None
    author_followers_count: Optional[int] = None
    author_following_count: Optional[int] = None
    author_tweet_count: Optional[int] = None
    author_profile_image_url: Optional[str] = None
    author_description: Optional[str] = None
    author_created_at: Optional[str] = None

    # Tweet content
    text: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None

    # Engagement
    like_count: Optional[int] = None
    retweet_count: Optional[int] = None
    reply_count: Optional[int] = None
    quote_count: Optional[int] = None
    bookmark_count: Optional[int] = None
    view_count: Optional[int] = None

    # Media
    has_media: bool = False
    media_count: int = 0
    media_urls: Optional[list] = None
    media_types: Optional[list] = None

    # Context
    is_retweet: bool = False
    is_quote: bool = False
    is_reply: bool = False
    reply_to_tweet_id: Optional[str] = None
    reply_to_user: Optional[str] = None
    quoted_tweet_id: Optional[str] = None
    conversation_id: Optional[str] = None

    # Hashtags and mentions
    hashtags: Optional[list] = None
    mentions: Optional[list] = None
    urls: Optional[list] = None

    # Extra
    possibly_sensitive: Optional[bool] = None
    raw_data: Optional[dict] = None


def extract_tweet_id(url: str) -> Optional[str]:
    """
    Extract the tweet ID from a URL.

    Supported formats:
    - https://twitter.com/user/status/1234567890
    - https://x.com/user/status/1234567890
    - https://mobile.twitter.com/user/status/1234567890
    - 1234567890 (direct ID)
    """
    if url.isdigit():
        return url

    patterns = [
        r'(?:twitter\.com|x\.com)/\w+/status/(\d+)',
        r'(?:mobile\.twitter\.com)/\w+/status/(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extract_username_from_url(url: str) -> Optional[str]:
    """Extract username from tweet URL."""
    pattern = r'(?:twitter\.com|x\.com)/(\w+)/status/'
    match = re.search(pattern, url)
    return match.group(1) if match else None


async def get_tweet_via_syndication(tweet_id: str) -> Optional[TweetMetadata]:
    """
    Retrieve tweet metadata using Twitter Syndication API.
    This public endpoint does not require authentication.
    """
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, follow_redirects=True)

            if response.status_code == 404:
                print(f"Tweet not found (may have been deleted or is private)")
                return None

            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                return None

            data = response.json()

            # Extract user information
            user = data.get("user", {})

            # Extract media
            media_urls = []
            media_types = []
            media_details = data.get("mediaDetails", [])
            for m in media_details:
                if m.get("media_url_https"):
                    media_urls.append(m["media_url_https"])
                if m.get("type"):
                    media_types.append(m["type"])

            # Video handling
            if data.get("video"):
                video = data["video"]
                variants = video.get("variants", [])
                # Get the variant with highest bitrate
                best_video = max(
                    [v for v in variants if v.get("bitrate")],
                    key=lambda x: x.get("bitrate", 0),
                    default=None
                )
                if best_video:
                    media_urls.append(best_video["url"])
                    media_types.append("video")

            # Extract hashtags
            hashtags = []
            entities = data.get("entities", {})
            for h in entities.get("hashtags", []):
                hashtags.append(h.get("text", ""))

            # Extract mentions
            mentions = []
            for m in entities.get("user_mentions", []):
                mentions.append(m.get("screen_name", ""))

            # Extract URLs
            urls_list = []
            for u in entities.get("urls", []):
                urls_list.append(u.get("expanded_url", u.get("url", "")))

            # Build metadata
            metadata = TweetMetadata(
                tweet_id=str(data.get("id_str", tweet_id)),
                tweet_url=f"https://x.com/{user.get('screen_name', 'unknown')}/status/{tweet_id}",
                source_method="syndication_api",

                # Author
                author_id=user.get("id_str"),
                author_username=user.get("screen_name"),
                author_display_name=user.get("name"),
                author_verified=user.get("verified") or user.get("is_blue_verified", False),
                author_followers_count=user.get("followers_count"),
                author_following_count=user.get("friends_count"),
                author_tweet_count=user.get("statuses_count"),
                author_profile_image_url=user.get("profile_image_url_https"),
                author_description=user.get("description"),

                # Content
                text=data.get("text"),
                language=data.get("lang"),
                created_at=data.get("created_at"),

                # Engagement
                like_count=data.get("favorite_count"),
                retweet_count=data.get("retweet_count"),
                reply_count=data.get("reply_count"),
                quote_count=data.get("quote_count"),
                bookmark_count=data.get("bookmark_count"),
                view_count=int(data["views"]["count"]) if data.get("views", {}).get("count") else None,

                # Media
                has_media=len(media_details) > 0 or bool(data.get("video")),
                media_count=len(media_details),
                media_urls=media_urls if media_urls else None,
                media_types=media_types if media_types else None,

                # Context
                is_reply=bool(data.get("in_reply_to_status_id_str")),
                is_quote=bool(data.get("quoted_tweet")),
                reply_to_tweet_id=data.get("in_reply_to_status_id_str"),
                reply_to_user=data.get("in_reply_to_screen_name"),
                conversation_id=data.get("conversation_id_str"),

                # Hashtags and mentions
                hashtags=hashtags if hashtags else None,
                mentions=mentions if mentions else None,
                urls=urls_list if urls_list else None,

                # Extra
                possibly_sensitive=data.get("possibly_sensitive"),
                raw_data=data,
            )

            return metadata

        except httpx.HTTPError as e:
            print(f"HTTP Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None


async def get_tweet_with_twscrape(tweet_id: str, api) -> Optional[TweetMetadata]:
    """
    Retrieve tweet metadata using twscrape.
    Requires accounts configured in the pool.
    """
    try:
        tweet = await api.tweet_details(int(tweet_id))

        if not tweet:
            return None

        # Extract media info
        media_urls = []
        media_types = []
        if tweet.media:
            for m in tweet.media:
                if hasattr(m, 'url'):
                    media_urls.append(m.url)
                if hasattr(m, 'type'):
                    media_types.append(m.type)

        # Extract hashtags
        hashtags = []
        if tweet.hashtags:
            hashtags = tweet.hashtags

        # Extract mentions
        mentions = []
        if tweet.mentionedUsers:
            mentions = [u.username for u in tweet.mentionedUsers]

        # Extract URLs
        urls_list = []
        if tweet.links:
            urls_list = [link.url for link in tweet.links]

        metadata = TweetMetadata(
            tweet_id=str(tweet.id),
            tweet_url=tweet.url,
            source_method="twscrape",

            # Author
            author_id=str(tweet.user.id) if tweet.user else None,
            author_username=tweet.user.username if tweet.user else None,
            author_display_name=tweet.user.displayname if tweet.user else None,
            author_verified=tweet.user.verified if tweet.user else None,
            author_followers_count=tweet.user.followersCount if tweet.user else None,
            author_following_count=tweet.user.friendsCount if tweet.user else None,
            author_tweet_count=tweet.user.statusesCount if tweet.user else None,
            author_profile_image_url=tweet.user.profileImageUrl if tweet.user else None,
            author_description=tweet.user.rawDescription if tweet.user else None,
            author_created_at=tweet.user.created.isoformat() if tweet.user and tweet.user.created else None,

            # Content
            text=tweet.rawContent,
            language=tweet.lang,
            source=tweet.source,
            created_at=tweet.date.isoformat() if tweet.date else None,

            # Engagement
            like_count=tweet.likeCount,
            retweet_count=tweet.retweetCount,
            reply_count=tweet.replyCount,
            quote_count=tweet.quoteCount,
            bookmark_count=tweet.bookmarkCount if hasattr(tweet, 'bookmarkCount') else None,
            view_count=tweet.viewCount,

            # Media
            has_media=bool(tweet.media),
            media_count=len(tweet.media) if tweet.media else 0,
            media_urls=media_urls if media_urls else None,
            media_types=media_types if media_types else None,

            # Context
            is_retweet=bool(tweet.retweetedTweet),
            is_quote=bool(tweet.quotedTweet),
            is_reply=bool(tweet.inReplyToTweetId),
            reply_to_tweet_id=str(tweet.inReplyToTweetId) if tweet.inReplyToTweetId else None,
            reply_to_user=tweet.inReplyToUser.username if tweet.inReplyToUser else None,
            quoted_tweet_id=str(tweet.quotedTweet.id) if tweet.quotedTweet else None,
            conversation_id=str(tweet.conversationId) if tweet.conversationId else None,

            # Hashtags and mentions
            hashtags=hashtags if hashtags else None,
            mentions=mentions if mentions else None,
            urls=urls_list if urls_list else None,

            # Extra
            possibly_sensitive=tweet.possiblySensitive if hasattr(tweet, 'possiblySensitive') else None,
        )

        return metadata

    except Exception as e:
        print(f"twscrape error: {e}")
        return None


def print_metadata(metadata: TweetMetadata):
    """Print metadata in readable format."""
    print("\n" + "="*60)
    print("TWEET METADATA")
    print(f"(source: {metadata.source_method})")
    print("="*60)

    print(f"\n IDENTIFIERS")
    print(f"   ID: {metadata.tweet_id}")
    print(f"   URL: {metadata.tweet_url}")

    if metadata.author_username:
        print(f"\n AUTHOR")
        print(f"   Username: @{metadata.author_username}")
        print(f"   Name: {metadata.author_display_name}")
        if metadata.author_id:
            print(f"   ID: {metadata.author_id}")
        if metadata.author_verified is not None:
            print(f"   Verified: {'Yes' if metadata.author_verified else 'No'}")
        if metadata.author_followers_count:
            print(f"   Followers: {metadata.author_followers_count:,}")
        if metadata.author_following_count:
            print(f"   Following: {metadata.author_following_count:,}")
        if metadata.author_tweet_count:
            print(f"   Total tweets: {metadata.author_tweet_count:,}")
        if metadata.author_description:
            bio = metadata.author_description[:100]
            print(f"   Bio: {bio}{'...' if len(metadata.author_description) > 100 else ''}")

    if metadata.text:
        print(f"\n CONTENT")
        text_preview = metadata.text[:200]
        print(f"   Text: {text_preview}{'...' if len(metadata.text) > 200 else ''}")
        if metadata.language:
            print(f"   Language: {metadata.language}")
        if metadata.created_at:
            print(f"   Date: {metadata.created_at}")
        if metadata.source:
            print(f"   Source: {metadata.source}")

    print(f"\n ENGAGEMENT")
    if metadata.like_count is not None:
        print(f"   Likes: {metadata.like_count:,}")
    if metadata.retweet_count is not None:
        print(f"   Retweets: {metadata.retweet_count:,}")
    if metadata.reply_count is not None:
        print(f"   Replies: {metadata.reply_count:,}")
    if metadata.quote_count is not None:
        print(f"   Quotes: {metadata.quote_count:,}")
    if metadata.view_count is not None:
        print(f"   Views: {metadata.view_count:,}")
    if metadata.bookmark_count is not None:
        print(f"   Bookmarks: {metadata.bookmark_count:,}")

    if metadata.has_media:
        print(f"\n MEDIA")
        print(f"   Contains media: Yes ({metadata.media_count} items)")
        if metadata.media_types:
            print(f"   Types: {', '.join(metadata.media_types)}")
        if metadata.media_urls:
            for i, url in enumerate(metadata.media_urls[:3], 1):
                print(f"   URL {i}: {url}")

    print(f"\n CONTEXT")
    print(f"   Is retweet: {'Yes' if metadata.is_retweet else 'No'}")
    print(f"   Is quote: {'Yes' if metadata.is_quote else 'No'}")
    print(f"   Is reply: {'Yes' if metadata.is_reply else 'No'}")
    if metadata.reply_to_user:
        print(f"   Reply to: @{metadata.reply_to_user}")
    if metadata.conversation_id:
        print(f"   Conversation ID: {metadata.conversation_id}")

    if metadata.hashtags:
        print(f"\n HASHTAGS")
        print(f"   {', '.join(['#' + h for h in metadata.hashtags])}")

    if metadata.mentions:
        print(f"\n MENTIONS")
        print(f"   {', '.join(['@' + m for m in metadata.mentions])}")

    if metadata.urls:
        print(f"\n URLs IN TWEET")
        for url in metadata.urls[:5]:
            print(f"   {url}")

    print("\n" + "="*60)


def save_metadata_json(metadata: TweetMetadata, output_file: str, include_raw: bool = False):
    """Save metadata to JSON format."""
    data = asdict(metadata)

    if not include_raw and 'raw_data' in data:
        del data['raw_data']

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nMetadata saved to: {output_file}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python get_tweet_metadata.py <tweet_url> [--raw]")
        print("Example: python get_tweet_metadata.py https://x.com/elonmusk/status/1234567890")
        print("\nOptions:")
        print("  --raw       Include raw data in JSON output")
        print("  --twscrape  Force use of twscrape (requires configured accounts)")
        sys.exit(1)

    tweet_input = sys.argv[1]
    include_raw = "--raw" in sys.argv
    force_twscrape = "--twscrape" in sys.argv

    # Extract tweet ID
    tweet_id = extract_tweet_id(tweet_input)
    if not tweet_id:
        print(f"Unable to extract tweet ID from: {tweet_input}")
        sys.exit(1)

    print(f"Searching for tweet ID: {tweet_id}")

    metadata = None

    # Method 1: Try twscrape if forced or available with accounts
    if force_twscrape and TWSCRAPE_AVAILABLE:
        print("Using twscrape...")
        api = API()
        accounts = await api.pool.accounts_info()
        if accounts:
            metadata = await get_tweet_with_twscrape(tweet_id, api)
        else:
            print("No twscrape accounts configured, falling back to syndication API...")

    # Method 2: Syndication API (fallback or default)
    if not metadata:
        print("Using Twitter Syndication API...")
        metadata = await get_tweet_via_syndication(tweet_id)

    if metadata:
        print_metadata(metadata)

        output_file = f"tweet_{tweet_id}_metadata.json"
        save_metadata_json(metadata, output_file, include_raw=include_raw)

        return metadata
    else:
        print(f"Unable to retrieve metadata for tweet {tweet_id}")
        print("\nPossible causes:")
        print("  - The tweet has been deleted")
        print("  - The tweet is private/protected")
        print("  - The account has been suspended")
        print("  - Rate limit reached")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
