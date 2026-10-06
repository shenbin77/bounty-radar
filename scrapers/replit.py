import hashlib
import json
import requests


# Replit uses Apollo Persisted Queries — we send the query + its SHA256 hash
_BOUNTIES_QUERY = """
query BountiesPageListingQuery($input: BountiesInput!) {
  bounties(input: $input) {
    items {
      id
      title
      cycles
      deadline
      description
      slug
      user { username }
      listing { state }
    }
  }
}
""".strip()

_QUERY_HASH = hashlib.sha256(_BOUNTIES_QUERY.encode()).hexdigest()

# 1 Replit Cycle = $0.01 USD
CYCLES_TO_USD = 0.01


def fetch(limit=20):
    """Fetch open bounties from Replit via GraphQL."""
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://replit.com/bounties",
        "Origin": "https://replit.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    payload = {
        "query": _BOUNTIES_QUERY,
        "variables": {
            "input": {
                "count": limit,
                "order": "Bounty",
                "listingState": "Listed",
            }
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": _QUERY_HASH,
            }
        },
    }

    results = []
    try:
        resp = requests.post(
            "https://replit.com/graphql",
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data and not data.get("data"):
            print(f"[Replit] GraphQL error: {data['errors']}")
            return _fallback()

        items = data.get("data", {}).get("bounties", {}).get("items", [])
        for item in items[:limit]:
            cycles = item.get("cycles", 0) or 0
            usd = cycles * CYCLES_TO_USD
            slug = item.get("slug", item.get("id", ""))
            results.append({
                "source": "Replit",
                "title": item.get("title", "N/A"),
                "url": f"https://replit.com/bounties/{slug}" if slug else "https://replit.com/bounties",
                "prize": f"${usd:,.0f}" if usd > 0 else "N/A",
                "deadline": item.get("deadline", "N/A"),
                "participants": None,
                "raw": f"{item.get('title', '')} {item.get('description', '')}".strip()[:500],
            })
    except Exception as e:
        print(f"[Replit] Error: {e}")
        return _fallback()

    return results if results else _fallback()


def _fallback():
    return [{
        "source": "Replit",
        "title": "Replit Open Bounties",
        "url": "https://replit.com/bounties",
        "prize": "Various",
        "deadline": "See website",
        "participants": None,
        "_is_pointer": True,
        "raw": "Replit hosts coding bounties where developers build apps for clients. 1 Cycle = $0.01 USD.",
    }]
