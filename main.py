import json
import os
import re
from datetime import datetime
from scrapers import dorahacks, gitcoin, superteam
import processor
import notifier


# ── Currency conversion ────────────────────────────────────────────────────────
# Approximate rates to USD (update periodically)
_CURRENCY_RATES = [
    ("₹",  1 / 85),    # INR
    ("€",  1.08),       # EUR
    ("£",  1.27),       # GBP
    ("¥",  1 / 150),    # JPY
    ("C$", 0.73),       # CAD
    ("A$", 0.64),       # AUD
    ("$",  1.0),        # USD — must be last to avoid matching C$/A$
]


def _to_usd(prize_str) -> tuple[float, str]:
    """Return (usd_value, display_string). Converts any currency to USD."""
    raw = str(prize_str or "").strip()
    if raw in ("", "N/A", "None", "See listing", "Various", "See website"):
        return 0.0, raw or "N/A"

    rate, symbol = 1.0, "$"
    for sym, r in _CURRENCY_RATES:
        if sym in raw:
            rate, symbol = r, sym
            break

    nums = re.findall(r"\d+", raw.replace(",", ""))
    if not nums:
        return 0.0, raw

    usd = float(nums[0]) * rate
    if symbol == "$":
        return usd, f"${int(usd):,}"
    else:
        return usd, f"${int(usd):,} (~{raw})"


# ── Deadline parsing ───────────────────────────────────────────────────────────
_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_end_date(deadline_str: str):
    """Parse the end date from a deadline string like 'Feb 09 - Mar 25, 2026'."""
    if not deadline_str or deadline_str in ("N/A", "None", "See listing", "See website"):
        return None

    parts = deadline_str.split(" - ")
    start_str = parts[0].strip()
    end_str = parts[-1].strip()

    # "Apr 07, 2026"
    try:
        return datetime.strptime(end_str, "%b %d, %Y")
    except ValueError:
        pass

    # "30, 2026" — same month as start
    m = re.match(r"(\d+),\s*(\d{4})", end_str)
    if m:
        day, year = int(m.group(1)), int(m.group(2))
        month_m = re.search(r"([A-Za-z]{3})", start_str)
        if month_m:
            month = _MONTH_MAP.get(month_m.group(1).lower())
            if month:
                try:
                    return datetime(year, month, day)
                except ValueError:
                    pass

    # ISO "2026-04-07T..."
    iso_m = re.search(r"(\d{4}-\d{2}-\d{2})", end_str)
    if iso_m:
        try:
            return datetime.strptime(iso_m.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    return None


# ── Filter & sort ──────────────────────────────────────────────────────────────
def filter_and_sort(items: list) -> list:
    """Remove expired/no-prize items, normalize prizes to USD, sort by prize."""
    now = datetime.utcnow()
    result = []

    for item in items:
        # Skip expired
        end_date = _parse_end_date(item.get("deadline", ""))
        if end_date and end_date < now:
            print(f"[Filter] Expired: {item['title']} (ended {end_date.date()})")
            continue

        # Normalize prize to USD
        usd_val, usd_display = _to_usd(item.get("prize"))
        item["prize"] = usd_display
        item["_prize_val"] = usd_val

        # Ending soon label
        if end_date:
            days_left = (end_date - now).days
            if days_left <= 14:
                item["_days_left"] = days_left

        is_prestige = item.get("prestige", False)
        is_pointer = item.get("_is_pointer", False)

        if is_pointer:
            item["_prize_val"] = 0
            result.append(item)
        elif usd_val > 0 or is_prestige:
            result.append(item)

    # Sort: real competitions first (by prize), pointers at the end
    result.sort(key=lambda x: (x.get("_is_pointer", False), -x["_prize_val"]))
    return result


# ── Deduplication ──────────────────────────────────────────────────────────────
SEEN_FILE = "seen.json"


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def deduplicate(items: list, seen: set) -> tuple[list, set]:
    new_items, new_seen = [], set(seen)
    for item in items:
        key = item.get("url") or item.get("title", "")
        if key and key not in new_seen:
            new_items.append(item)
            new_seen.add(key)
    return new_items, new_seen


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=== Hackathon Aggregator Starting ===")
    seen = load_seen()

    all_items = []
    # Focused scrapers: content-friendly bounty sources only.
    # (devpost/mlh/replit/reddit/github_search/twitter are coding-hackathon
    # oriented in the upstream repo — not our battlefield.)
    for scraper in [superteam, gitcoin, dorahacks]:
        name = scraper.__name__.split(".")[-1]
        try:
            items = scraper.fetch()
            print(f"[{name}] fetched {len(items)} items")
            all_items.extend(items)
        except Exception as e:
            print(f"[{name}] failed: {e}")

    print(f"Total raw items: {len(all_items)}")

    new_items, updated_seen = deduplicate(all_items, seen)
    print(f"New (unseen) items: {len(new_items)}")

    enriched = processor.analyze(new_items)
    relevant = [it for it in enriched if it.get("relevant", True)]
    print(f"Relevant items after filtering: {len(relevant)}")

    final = filter_and_sort(relevant)
    print(f"Final items after prize/expiry filter: {len(final)}")

    notifier.send_digest(final)
    save_seen(updated_seen)
    print("=== Done ===")


if __name__ == "__main__":
    main()
