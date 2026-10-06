import os
import json

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def _get_client():
    from openai import OpenAI
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

SYSTEM_PROMPT = """You are an assistant that analyzes Web3 bounties (mostly content, design, translation, community tasks — NOT coding).
For each item, provide the following IN ENGLISH:
- description: what the bounty asks for (1-2 sentences, based on title and context)
- level: required skill level — one of: Beginner / Intermediate / Advanced
- technologies: skills needed, e.g. "Twitter/X threads", "video editing", "ZH/EN translation", "graphic design" (comma-separated, or "Not specified")
- relevant: true if this is a real content/design/community bounty a beginner could attempt, false if spam, coding-only, or unrelated
- prestige: true if the sponsor is a well-known crypto project or brand that is valuable for a freelancer's portfolio (e.g. Solana Foundation, major exchanges, top DeFi protocols), false otherwise

DO NOT include prize or deadline fields — those are already provided.
Respond with a JSON array of objects with exactly these keys: description, level, technologies, relevant, prestige.
Be concise. Always write in English."""


def analyze(items: list) -> list:
    """Send items to DeepSeek for analysis. Returns enriched list."""
    if not DEEPSEEK_API_KEY:
        print("[Processor] DEEPSEEK_API_KEY not set, skipping enrichment.")
        return _fallback(items)

    client = _get_client()
    results = []
    batch_size = 10
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        payload = json.dumps([
            {"index": j, "title": it["title"], "raw": it["raw"], "source": it["source"]}
            for j, it in enumerate(batch)
        ], ensure_ascii=False)

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze these competitions:\n{payload}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            analyzed = parsed if isinstance(parsed, list) else parsed.get("items", parsed.get("competitions", []))
            for j, item in enumerate(batch):
                enriched = analyzed[j] if j < len(analyzed) else {}
                if not enriched.get("relevant", True):
                    continue
                # Merge: scraper data wins for prize/deadline/participants
                merged = {**item, **enriched}
                for key in ("prize", "deadline", "participants"):
                    if item.get(key) not in (None, "N/A", ""):
                        merged[key] = item[key]
                results.append(merged)
        except Exception as e:
            print(f"[Processor] Batch {i // batch_size} error: {e}")
            results.extend(batch)

    return results


def _fallback(items: list) -> list:
    """Return items as-is when no API key is available."""
    return [{"relevant": True, "level": "Unknown", "technologies": "N/A",
             "description": it.get("raw", "")[:200], **it} for it in items]
