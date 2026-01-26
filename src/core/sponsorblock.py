"""
core/sponsorblock.py
Thin client for the SponsorBlock API (https://sponsor.ajay.app/).
Only works for YouTube video IDs — SponsorBlock has no data for other sources.
"""
import aiohttp
import logging
import re

log = logging.getLogger("simvox.sponsorblock")

API_BASE = "https://sponsor.ajay.app/api"

# Segment categories we care about for a music bot. "music_offtopic" covers
# non-music intros/outros on lyric videos; "selfpromo" + "interaction" cover
# the standard YouTube monetization clutter.
CATEGORIES = ["sponsor", "selfpromo", "interaction", "intro", "outro", "music_offtopic"]

_YT_ID_RE = re.compile(r"(?:v=|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})")


def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    match = _YT_ID_RE.search(url)
    return match.group(1) if match else None


async def get_segments(video_id: str) -> list[dict]:
    """
    Returns a list of {"start": float, "end": float, "category": str} segments
    to skip, sorted by start time. Empty list on any failure (fail open).
    """
    if not video_id:
        return []

    params = {
        "videoID": video_id,
        "categories": str(CATEGORIES).replace("'", '"'),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/skipSegments", params=params, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 404:
                    return []  # no segments submitted for this video
                if resp.status != 200:
                    log.warning(f"SponsorBlock returned {resp.status} for {video_id}")
                    return []
                data = await resp.json()
    except Exception as e:
        log.warning(f"SponsorBlock fetch failed for {video_id}: {e}")
        return []

    segments = []
    for item in data:
        seg = item.get("segment", [])
        if len(seg) == 2:
            segments.append({
                "start": seg[0],
                "end": seg[1],
                "category": item.get("category", "unknown"),
            })

    segments.sort(key=lambda s: s["start"])
    return segments


def next_segment_after(segments: list[dict], position: float) -> dict | None:
    """Find the next segment whose start is >= position (with small tolerance)."""
    for seg in segments:
        if seg["start"] >= position - 0.5:
            return seg
    return None


def segment_containing(segments: list[dict], position: float) -> dict | None:
    """If position currently sits inside a segment, return it (for late joins / seeks)."""
    for seg in segments:
        if seg["start"] <= position < seg["end"]:
            return seg
    return None