import requests
from bs4 import BeautifulSoup


def fetch(limit=20):
    """Fetch upcoming hackathons from MLH (Major League Hacking)."""
    url = "https://mlh.io/seasons/2026/events"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HackathonBot/1.0)"}
    results = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".event")[:limit]:
            title_el = card.select_one(".event-name")
            date_el = card.select_one(".event-date")
            link_el = card.select_one("a[href]")
            location_el = card.select_one(".event-location")
            results.append({
                "source": "MLH",
                "title": title_el.get_text(strip=True) if title_el else "MLH Hackathon",
                "url": link_el["href"] if link_el else "https://mlh.io/seasons/2026/events",
                "prize": "Prizes + Swag",
                "deadline": date_el.get_text(strip=True) if date_el else "N/A",
                "raw": card.get_text(separator=" ", strip=True)[:500],
            })
    except Exception as e:
        print(f"[MLH] Error: {e}")
    return results
