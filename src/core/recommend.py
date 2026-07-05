"""
core/recommend.py
Smarter autoplay recommendations than a raw title search.

Strategy: build a "radio mix" style query from the artist + a generic "mix"
or "radio" suffix, which YouTube's search ranking tends to resolve to
similar-artist or similar-genre tracks rather than just exact title matches.
We also de-duplicate against recent history so the bot doesn't loop the
same 3 songs.
"""
import asyncio
import logging
import re

log = logging.getLogger("simvox.recommend")


def _clean_title(title: str) -> str:
    """Strip common noise: (Official Video), [Lyrics], feat., etc."""
    cleaned = re.sub(r"[\(\[].*?[\)\]]", "", title)
    cleaned = re.sub(r"\bfeat\.?.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bofficial\b|\blyrics?\b|\bvideo\b|\baudio\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" -|")


async def get_recommendations(
    current_track: dict,
    history: list[dict],
    max_results: int = 5,
) -> list[dict]:
    """
    Returns up to max_results track dicts recommended based on current_track,
    excluding anything already in recent history (last 20 plays) or matching
    the current track's title.
    """
    from core.scraper import search_top_tracks

    title    = current_track.get("title", "")
    uploader = current_track.get("uploader", "")
    clean    = _clean_title(title)

    queries = [
        f"{uploader} mix",
        f"{uploader} radio",
        f"{clean} similar songs",
    ]

    seen_titles = {h["title"] for h in history[-20:]} | {title}
    results: list[dict] = []

    for query in queries:
        try:
            candidates = await asyncio.to_thread(search_top_tracks, query, 8)
        except Exception as e:
            log.warning(f"Recommendation query failed ({query}): {e}")
            continue

        for c in candidates:
            if c["title"] in seen_titles:
                continue
            # Avoid near-duplicate titles (same song, different upload)
            if any(_similar(c["title"], r["title"]) for r in results):
                continue
            results.append(c)
            seen_titles.add(c["title"])
            if len(results) >= max_results:
                return results

        if len(results) >= max_results:
            break

    return results


def _similar(a: str, b: str) -> bool:
    """Cheap similarity check — same first 4 words, case-insensitive."""
    wa = _clean_title(a).lower().split()[:4]
    wb = _clean_title(b).lower().split()[:4]
    return wa == wb and len(wa) > 0