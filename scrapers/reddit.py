"""
reddit.py — Fetches posts via Reddit RSS feeds.

No API key required. Reddit blocks requests from cloud servers (GitHub Actions),
but RSS feeds work fine through feedparser.
"""
import time
import feedparser

FEEDS = [
    {"sub": "r/ethdev",         "url": "https://www.reddit.com/r/ethdev/top.rss?t=week"},
    {"sub": "r/web3",           "url": "https://www.reddit.com/r/web3/top.rss?t=week"},
    {"sub": "r/hackathon",      "url": "https://www.reddit.com/r/hackathon/top.rss?t=week"},
    {"sub": "r/webdev",         "url": "https://www.reddit.com/r/webdev/top.rss?t=week"},
    {"sub": "r/cryptocurrency", "url": "https://www.reddit.com/r/cryptocurrency/top.rss?t=week"},
    {"sub": "r/learnprogramming","url": "https://www.reddit.com/r/learnprogramming/top.rss?t=week"},
]

KEYWORDS = ["hackathon", "bounty", "contest", "competition", "challenge", "prize", "vibe cod"]


def fetch(limit=30):
    """Search Reddit top posts via RSS for competition-related content."""
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; HackathonBot/1.0)"
    results = []

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
                if any(kw in text for kw in KEYWORDS):
                    results.append({
                        "source": f"Reddit {feed_info['sub']}",
                        "title": entry.get("title", "N/A").strip(),
                        "url": entry.get("link", ""),
                        "prize": "N/A",
                        "deadline": "N/A",
                        "raw": (entry.get("title", "") + " " + entry.get("summary", ""))[:500],
                    })
        except Exception as e:
            print(f"[Reddit RSS] {feed_info['sub']} error: {e}")
        time.sleep(0.5)

    return results[:limit]
