"""
core/resolver.py
Detects the source of a query (plain text search, YouTube URL, SoundCloud URL,
Spotify URL) and routes it to the right fetch strategy.

Spotify support uses `spotifyscraper` (no API key needed).
Install: pip install spotifyscraper
"""
import re
import logging
import asyncio
from enum import Enum, auto

log = logging.getLogger("simvox.resolver")

_YOUTUBE_RE    = re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE)
_SOUNDCLOUD_RE = re.compile(r"soundcloud\.com", re.IGNORECASE)
_SPOTIFY_RE    = re.compile(r"open\.spotify\.com", re.IGNORECASE)

# Extracts entity type + bare ID from Spotify URLs
# Handles ?si= query params and any trailing junk
_SPOTIFY_ENTITY_RE = re.compile(
    r"open\.spotify\.com/(?:intl-[a-z]+/)?(?:embed/)?(track|album|playlist)/([A-Za-z0-9]+)",
    re.IGNORECASE,
)


class SourceType(Enum):
    SEARCH     = auto()
    YOUTUBE    = auto()
    SOUNDCLOUD = auto()
    SPOTIFY    = auto()


def detect_source(query: str) -> SourceType:
    if not query.startswith("http"):
        return SourceType.SEARCH
    if _SPOTIFY_RE.search(query):
        return SourceType.SPOTIFY
    if _YOUTUBE_RE.search(query):
        return SourceType.YOUTUBE
    if _SOUNDCLOUD_RE.search(query):
        return SourceType.SOUNDCLOUD
    return SourceType.YOUTUBE  # default: let yt-dlp try, it supports 1000+ sites


async def resolve(query: str) -> list[dict]:
    """
    Single entry point used by the play command. Returns a list of track
    dicts ready to queue. Raises RuntimeError with a user-facing message
    on failure.
    """
    from core.scraper import search_top_tracks, fetch_by_url

    source = detect_source(query)

    if source == SourceType.SPOTIFY:
        return await resolve_spotify(query)

    if source in (SourceType.YOUTUBE, SourceType.SOUNDCLOUD):
        track = await asyncio.to_thread(fetch_by_url, query)
        return [track]

    # plain text search — returns multiple results for the search UI
    return await asyncio.to_thread(search_top_tracks, query, 10)


# ── Spotify ──────────────────────────────────────────────────────────────────

async def resolve_spotify(url: str) -> list[dict]:
    """
    Resolve a Spotify track, album, or playlist URL into playable track dicts.
    Uses spotifyscraper to get metadata, then searches YouTube for audio.
    """
    try:
        from spotify_scraper import SpotifyClient  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Spotify support requires `spotifyscraper`. Run: `pip install spotifyscraper`"
        )

    match = _SPOTIFY_ENTITY_RE.search(url)
    if not match:
        raise RuntimeError(
            "Couldn't parse that Spotify URL. Paste a track, album, or playlist link."
        )

    entity_type = match.group(1).lower()   # "track", "album", "playlist"
    entity_id   = match.group(2)           # bare alphanumeric ID, no query params

    log.info(f"Spotify resolve: type={entity_type} id={entity_id}")

    try:
        metas = await asyncio.to_thread(_fetch_spotify_meta, entity_type, entity_id)
    except Exception as e:
        log.warning(f"Spotify scrape failed ({entity_type}/{entity_id}): {e}")
        raise RuntimeError(f"Couldn't load Spotify metadata: {e}")

    if not metas:
        raise RuntimeError("No tracks found at that Spotify URL.")

    log.info(f"Spotify: got {len(metas)} track(s) to resolve")

    if len(metas) == 1:
        track = await _meta_to_yt(metas[0])
        return [track]

    # Multi-track: resolve concurrently, bounded to 5 at a time
    return await _resolve_batch(metas, concurrency=5)


def _fetch_spotify_meta(entity_type: str, entity_id: str) -> list[dict]:
    """
    Synchronous (runs in a thread). Fetches Spotify metadata and returns
    a list of minimal dicts: {title, artist, duration_ms, search_query}.

    Uses the bare entity ID, not the full URL, to avoid embed-page 
    "unavailable" errors that occur when passing full playlist URLs.
    """
    from spotify_scraper import SpotifyClient

    with SpotifyClient() as client:
        if entity_type == "track":
            track = client.get_track(entity_id)
            return [_to_meta(track)]

        elif entity_type == "album":
            album = client.get_album(entity_id)
            return [_to_meta(t) for t in album.tracks if t]

        elif entity_type == "playlist":
            playlist = client.get_playlist(entity_id)
            metas = []
            for item in playlist.tracks:
                # spotifyscraper playlist items may be Track objects or
                # PlaylistTrack wrappers — handle both
                track = getattr(item, "track", item)
                if track and getattr(track, "name", None):
                    metas.append(_to_meta(track))
            return metas

    return []


def _to_meta(track) -> dict:
    """Convert a spotifyscraper Track-like object to a search-ready dict."""
    name   = getattr(track, "name", "Unknown")
    artists = getattr(track, "artists", [])
    artist  = artists[0].name if artists else "Unknown Artist"
    dur_ms  = getattr(track, "duration_ms", 0) or 0
    return {
        "title":        name,
        "artist":       artist,
        "duration_ms":  dur_ms,
        "search_query": f"{artist} - {name}",
    }


async def _meta_to_yt(meta: dict) -> dict:
    """Search YouTube for a track meta dict and return a playable track dict."""
    from core.scraper import search_top_tracks
    results = await asyncio.to_thread(search_top_tracks, meta["search_query"], 1)
    if not results:
        raise RuntimeError(f"Couldn't find '{meta['search_query']}' on YouTube.")
    track = results[0]
    # Fill in Spotify's duration if yt-dlp returns 0
    if not track.get("duration") and meta["duration_ms"]:
        track["duration"] = meta["duration_ms"] // 1000
    return track


async def _resolve_batch(metas: list[dict], concurrency: int = 5) -> list[dict]:
    """
    Resolve a batch of Spotify metas to YouTube tracks concurrently.
    Failed individual lookups are skipped — the rest still load.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict | None] = [None] * len(metas)

    async def _one(index: int, meta: dict):
        async with semaphore:
            try:
                results[index] = await _meta_to_yt(meta)
            except Exception as e:
                log.warning(f"Skipping '{meta.get('search_query', '?')}': {e}")

    await asyncio.gather(*[_one(i, m) for i, m in enumerate(metas)])
    resolved = [r for r in results if r is not None]
    log.info(f"Spotify batch: resolved {len(resolved)}/{len(metas)} tracks")
    return resolved