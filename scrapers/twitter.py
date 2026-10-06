import feedparser
import urllib.parse


NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
]

QUERIES = [
    "hackathon coding contest",
    "vibe coding bounty",
    "build challenge prize",
    "web3 hackathon",
]


def _try_nitter_rss(instance: str, query: str) -> list:
    encoded = urllib.parse.quote(query)
    url = f"{instance}/search/rss?q={encoded}&f=tweets"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:5]:
        results.append({
            "source": "Twitter/X",
            "title": entry.get("title", "N/A")[:120],
            "url": entry.get("link", ""),
            "prize": "N/A",
            "deadline": "N/A",
            "raw": entry.get("summary", "")[:500],
        })
    return results


def fetch(limit=20):
    """Search Twitter via Nitter RSS feeds (no API key required)."""
    results = []
    for query in QUERIES:
        found = False
        for instance in NITTER_INSTANCES:
            try:
                items = _try_nitter_rss(instance, query)
                if items:
                    results.extend(items)
                    found = True
                    break
            except Exception:
                continue
        if not found:
            print(f"[Twitter] All Nitter instances failed for query: {query}")
        if len(results) >= limit:
            break
    return results[:limit]
