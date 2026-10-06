import requests
from datetime import datetime

# Keep content / non-coding bounties: threads, videos, articles, design, etc.
# (The original upstream repo filtered these OUT — we want exactly them.)
_WANT_ANY = [
    "thread", "tweet", "ambassador", "video", "article", "write",
    "sticker", "design", "feedback", "spotlight", "story of",
    "content bounty", "illustration", "animation", "pitch contest",
    "market research", "interview", "what solana means", "explain",
    "share your experience", "translation", "translate", "meme",
    "infographic", "tutorial", "guide", "review", "reaction",
]

# Skip pure-dev tasks (we can't compete there yet)
_SKIP_ANY = [
    "smart contract", "anchor program", "rust ", "sdk",
    "dapp", "deploy", "vault program", "escrow program",
]

MIN_PRIZE_USD = 100


def _is_wanted(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in _SKIP_ANY):
        return False
    return any(kw in t for kw in _WANT_ANY)


def _fmt_date(iso: str) -> str:
    """Convert '2026-04-06T23:59:59.000Z' → 'Apr 06, 2026'."""
    if not iso or iso in ("N/A", "See website"):
        return iso
    try:
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return iso


def fetch(limit=20):
    """Fetch open content bounties from Superteam Earn (Solana ecosystem)."""
    url = "https://earn.superteam.fun/api/listings/"
    params = {"type": "bounty", "status": "open", "limit": 60}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HackathonBot/1.0)"}
    results = []

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        items = resp.json()
        if not isinstance(items, list):
            items = items.get("bounties", items.get("data", []))

        for item in items:
            reward = item.get("rewardAmount", 0) or 0
            title = item.get("title", "N/A")
            token = item.get("token", "USDC")

            if reward < MIN_PRIZE_USD:
                continue
            if not _is_wanted(title):
                continue

            slug = item.get("slug", item.get("id", ""))
            sponsor = item.get("sponsor", {}).get("name", "")
            submissions = item.get("_count", {}).get("Submission", None)
            deadline_raw = item.get("deadline", "N/A")

            results.append({
                "source": "Superteam Earn",
                "title": title,
                "url": f"https://earn.superteam.fun/listing/{slug}" if slug else "https://earn.superteam.fun/",
                "prize": f"${reward:,.0f} {token}",
                "deadline": _fmt_date(deadline_raw),
                "participants": submissions,
                "raw": f"{title} {sponsor} Solana Web3 content bounty".strip()[:500],
            })

            if len(results) >= limit:
                break

    except Exception as e:
        print(f"[Superteam] Error: {e}")

    return results
