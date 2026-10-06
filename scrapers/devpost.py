import re
import requests


def _parse_prize(raw: str) -> str:
    """Strip HTML and return prize string."""
    if not raw:
        return "N/A"
    text = re.sub(r"<[^>]+>", "", raw).strip()
    return text if text else "N/A"


def fetch(limit=20):
    """Fetch open hackathons from Devpost JSON API."""
    url = "https://devpost.com/api/hackathons"
    params = {
        "status[]": "open",
        "order_by": "prize_amount",
        "per_page": limit,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    results = []
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("hackathons", [])[:limit]:
            prize = _parse_prize(item.get("prize_amount", ""))
            themes = [t["name"] for t in item.get("themes", [])]
            deadline = item.get("submission_period_dates", "N/A")
            participants = item.get("registrations_count", None)
            results.append({
                "source": "Devpost",
                "title": item.get("title", "N/A"),
                "url": item.get("url", ""),
                "prize": prize,
                "deadline": deadline,
                "participants": participants,
                "raw": f"{item.get('title', '')} {' '.join(themes)} {item.get('organization_name', '')} prize:{prize} deadline:{deadline}".strip()[:500],
            })
    except Exception as e:
        print(f"[Devpost] Error: {e}")
    return results
