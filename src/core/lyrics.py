"""
core/lyrics.py
Fetches real lyrics text (not just links) using the free lyrics.ovh API.
No API key required. Falls back gracefully with a clear message if a
track has no match (instrumental, obscure, lyrics.ovh has no entry, etc).
"""
import aiohttp
import logging
import re

log = logging.getLogger("simvox.lyrics")

API_BASE = "https://api.lyrics.ovh/v1"

PAGE_CHAR_LIMIT = 1800  # keep embeds well under Discord's 4096 description limit


def _split_artist_title(raw_title: str) -> tuple[str, str]:
    """
    Best-effort split of a YouTube-style title into (artist, song).
    Handles 'Artist - Song', 'Artist – Song', 'Artist: Song' patterns,
    strips common noise like (Official Video), [Lyrics], etc.
    """
    cleaned = re.sub(r"[\(\[].*?[\)\]]", "", raw_title).strip()
    for sep in (" - ", " – ", " — ", ": "):
        if sep in cleaned:
            artist, song = cleaned.split(sep, 1)
            return artist.strip(), song.strip()
    return "", cleaned.strip()


async def fetch_lyrics(query: str) -> tuple[str, str] | None:
    """
    query is either 'Artist - Song' or just a song title.
    Returns (resolved_title, lyrics_text) or None if not found.
    """
    artist, song = _split_artist_title(query)
    if not artist:
        # No clear artist — try the whole string as the song with empty artist
        song = query
        artist = ""

    url = f"{API_BASE}/{artist}/{song}" if artist else f"{API_BASE}/{song}/{song}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception as e:
        log.warning(f"Lyrics fetch failed for '{query}': {e}")
        return None

    lyrics = data.get("lyrics", "").strip()
    if not lyrics:
        return None

    resolved_title = f"{artist} - {song}" if artist else song
    return resolved_title, lyrics


def paginate_lyrics(lyrics: str, page_size: int = PAGE_CHAR_LIMIT) -> list[str]:
    """Split lyrics into pages, preferring to break on blank lines (verse/chorus breaks)."""
    if len(lyrics) <= page_size:
        return [lyrics]

    pages = []
    remaining = lyrics
    while remaining:
        if len(remaining) <= page_size:
            pages.append(remaining)
            break
        chunk = remaining[:page_size]
        split_at = chunk.rfind("\n\n")
        if split_at < page_size * 0.5:  # no good blank-line break found, fall back to last newline
            split_at = chunk.rfind("\n")
        if split_at <= 0:
            split_at = page_size
        pages.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return pages