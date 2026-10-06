import requests
import os


# Specific queries targeting real competitions with prizes
QUERIES = [
    "hackathon bounty prize 2026 in:readme",
    "coding competition cash prize open in:readme",
    "vibe coding contest prize in:readme",
    "web3 hackathon bounty reward in:readme",
]


def fetch(limit=15):
    """Search GitHub repos that describe real competitions with prizes."""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results = []
    seen_urls = set()

    try:
        for query in QUERIES:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"{query} pushed:>2026-01-01",
                "sort": "updated",
                "order": "desc",
                "per_page": 5,
            }
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 422:
                continue
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                html_url = item.get("html_url", "")
                desc = (item.get("description") or "").lower()
                name = (item.get("name") or "").lower()
                # Skip if no description or looks like a personal project unrelated to competitions
                if not desc:
                    continue
                if not any(kw in desc + name for kw in ["hack", "bounty", "prize", "contest", "competition", "challenge"]):
                    continue
                if html_url in seen_urls:
                    continue
                seen_urls.add(html_url)
                results.append({
                    "source": "GitHub",
                    "title": item.get("full_name", "N/A"),
                    "url": html_url,
                    "prize": "N/A",
                    "deadline": "N/A",
                    "raw": f"{item.get('name', '')} {item.get('description', '')} {item.get('topics', [])}".strip()[:500],
                })
            if len(results) >= limit:
                break
    except Exception as e:
        print(f"[GitHub] Error: {e}")

    return results[:limit]
