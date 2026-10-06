import html
import os
import re
import requests
from datetime import datetime


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID")


def _send(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Notifier] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if TELEGRAM_THREAD_ID:
        payload["message_thread_id"] = int(TELEGRAM_THREAD_ID)
    resp = requests.post(url, json=payload, timeout=15)
    if not resp.ok:
        print(f"[Notifier] Telegram error: {resp.text}")


def _source_stats(items: list) -> str:
    counts = {}
    for it in items:
        src = it.get("source", "Unknown")
        counts[src] = counts.get(src, 0) + 1
    return ", ".join(f"{k} ({v})" for k, v in sorted(counts.items()))


def _format_block(i: int, item: dict) -> str:
    title = _strip_html(item.get("title", "N/A"))[:80]
    description = _strip_html(item.get("description", item.get("raw", "")))[:200]
    prize = item.get("prize", "N/A")
    deadline = item.get("deadline", "N/A")
    days_left = item.get("_days_left")
    deadline_display = deadline
    if days_left is not None:
        deadline_display += f" ⏰ {days_left}d left!"
    level = item.get("level", "N/A")
    technologies = item.get("technologies", "N/A")
    participants = item.get("participants")
    url = item.get("url", "")

    block = (
        f"<b>{i}. {title}</b>\n"
        f"📋 {description}\n"
        f"💰 Prize: {prize}\n"
        f"📅 Deadline: {deadline_display}\n"
        f"🎯 Level: {level}"
    )
    if technologies and technologies not in ("N/A", "Not specified"):
        block += f" | {technologies}"
    if participants:
        block += f"\n👥 Participants: {participants:,}" if isinstance(participants, int) else f"\n👥 Participants: {participants}"
    if url:
        block += f"\n🔗 {url}"
    block += "\n\n"
    return block


def _flush(messages: list, current: str) -> str:
    """Send current message and reset buffer."""
    _send(current.rstrip())
    return ""


def _save_local_digest(main_items: list, pointer_items: list, today: str):
    """Write a markdown copy of the digest next to the script."""
    lines = [f"# Weekly Content Bounties | {today}\n"]
    for i, item in enumerate(main_items, 1):
        title = _strip_html(item.get("title", "N/A"))
        desc = _strip_html(item.get("description", item.get("raw", "")))[:200]
        lines.append(f"## {i}. {title}")
        lines.append(f"- 💰 {item.get('prize', 'N/A')} | 📅 {item.get('deadline', 'N/A')}")
        lines.append(f"- 🎯 {item.get('level', 'N/A')} | {item.get('technologies', '')}")
        if item.get("participants"):
            lines.append(f"- 👥 {item.get('participants')} submissions")
        lines.append(f"- 📋 {desc}")
        lines.append(f"- 🔗 {item.get('url', '')}\n")
    if pointer_items:
        lines.append("## Also check")
        for it in pointer_items:
            lines.append(f"- {it.get('title', 'N/A')} — {it.get('url', '')}")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digest.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[Notifier] Local digest saved to {path}")


def send_digest(items: list):
    """Format and send weekly digest to Telegram; always save a local copy."""
    today = datetime.utcnow().strftime("%d %b %Y")

    main_items = [it for it in items if not it.get("_is_pointer")]
    pointer_items = [it for it in items if it.get("_is_pointer")]

    # Always keep a local markdown copy next to the script
    _save_local_digest(main_items, pointer_items, today)

    if not main_items and not pointer_items:
        _send(f"🎯 <b>Weekly Content Bounties | {today}</b>\n\nNo new bounties found this week.")
        return

    MAX_LEN = 4000
    header = f"🎯 <b>Weekly Content Bounties | {today}</b>\n\n"
    current_msg = header

    for i, item in enumerate(main_items, 1):
        block = _format_block(i, item)
        if len(current_msg) + len(block) > MAX_LEN:
            _send(current_msg.rstrip())
            current_msg = block
        else:
            current_msg += block

    # Stats line
    stats = f"Total: {len(main_items)} bounties\nSources: {_source_stats(main_items)}"
    if len(current_msg) + len(stats) > MAX_LEN:
        _send(current_msg.rstrip())
        current_msg = stats
    else:
        current_msg += stats

    # "Also check" section for pointer items
    if pointer_items:
        also_check = "\n\n🔍 <b>Also check:</b>\n"
        for it in pointer_items:
            also_check += f"• {it.get('title', 'N/A')} — {it.get('url', '')}\n"
        if len(current_msg) + len(also_check) > MAX_LEN:
            _send(current_msg.rstrip())
            _send(also_check.strip())
        else:
            _send((current_msg + also_check).rstrip())
    else:
        _send(current_msg.rstrip())
