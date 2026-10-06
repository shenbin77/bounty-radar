import requests


def fetch(limit=20):
    """Fetch bounties from Gitcoin API."""
    results = []

    # Gitcoin v1 bounties API
    url = "https://gitcoin.co/api/v0.1/bounties/"
    params = {
        "is_open": "true",
        "limit": limit,
        "order_by": "-web3_created",
        "network": "mainnet",
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HackathonBot/1.0)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        items = resp.json()
        if isinstance(items, dict):
            items = items.get("results", [])
        for item in items[:limit]:
            results.append({
                "source": "Gitcoin",
                "title": item.get("title", "N/A"),
                "url": item.get("url", "https://gitcoin.co/explorer"),
                "prize": f"{item.get('value_in_usdt', 'N/A')} USD",
                "deadline": item.get("expires_date", "N/A"),
                "raw": f"{item.get('title', '')} {item.get('description', '')}".strip()[:500],
            })
    except Exception as e:
        print(f"[Gitcoin] API error: {e}")

    # Fallback: return explorer link as a source
    if not results:
        results.append({
            "source": "Gitcoin",
            "title": "Gitcoin Open Bounties",
            "url": "https://gitcoin.co/explorer?network=mainnet&order_by=-web3_created&is_open=true",
            "prize": "Various",
            "deadline": "See website",
            "_is_pointer": True,
            "raw": "Gitcoin hosts Web3 open source bounties. Visit the explorer to see currently open bounties.",
        })

    return results
