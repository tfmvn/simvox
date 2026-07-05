"""
core/scraper.py
yt-dlp wrapper — search, direct URL (YouTube + SoundCloud), related tracks,
quality-tiered format selection.
"""
import yt_dlp
import logging

log = logging.getLogger("simvox.scraper")

# Quality tiers map to yt-dlp format selectors. "source" grabs whatever
# yt-dlp considers best regardless of bitrate (could be huge); the others
# cap bitrate to keep bandwidth/CPU sane on small VPS hosts.
QUALITY_FORMATS = {
    "low":    "worstaudio/worst",
    "medium": "bestaudio[abr<=96]/bestaudio/best",
    "high":   "bestaudio[abr<=192]/bestaudio/best",
    "source": "bestaudio/best",
}

_BASE_OPTS = {
    "noplaylist": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "skip_download": True,
}

# One YoutubeDL instance per quality tier so format selection is baked in.
_ytdl_instances = {
    quality: yt_dlp.YoutubeDL({**_BASE_OPTS, "format": fmt})
    for quality, fmt in QUALITY_FORMATS.items()
}


def _get_ytdl(quality: str = "high") -> yt_dlp.YoutubeDL:
    return _ytdl_instances.get(quality, _ytdl_instances["high"])


def _build_track(entry: dict) -> dict:
    return {
        "source":      entry.get("url", ""),
        "title":       entry.get("title", "Unknown Title"),
        "duration":    entry.get("duration", 0) or 0,
        "thumbnail":   entry.get("thumbnail"),
        "webpage_url": entry.get("webpage_url", entry.get("url", "")),
        "uploader":    entry.get("uploader", "Unknown Artist"),
        "view_count":  entry.get("view_count", 0),
        "upload_date": entry.get("upload_date"),       # YYYYMMDD string
        "like_count":  entry.get("like_count", 0),
        "extractor":   entry.get("extractor_key", entry.get("ie_key", "")),
    }


def search_top_tracks(query: str, max_results: int = 10, quality: str = "high") -> list[dict]:
    """Return up to max_results tracks matching query."""
    search_query = query if query.startswith("http") else f"ytsearch{max_results}:{query}"
    ytdl = _get_ytdl(quality)
    try:
        info = ytdl.extract_info(search_query, download=False)
    except Exception as e:
        log.error(f"yt-dlp search error: {e}")
        raise RuntimeError(f"Search failed: {e}") from e

    tracks = []
    if "entries" in info:
        for entry in info["entries"]:
            if entry:
                tracks.append(_build_track(entry))
    else:
        tracks.append(_build_track(info))

    if not tracks:
        raise RuntimeError("No results found.")
    return tracks


def fetch_by_url(url: str, quality: str = "high") -> dict:
    """Fetch a single track directly by URL. Works for YouTube and SoundCloud."""
    ytdl = _get_ytdl(quality)
    try:
        info = ytdl.extract_info(url, download=False)
        entry = info["entries"][0] if "entries" in info else info
        return _build_track(entry)
    except Exception as e:
        log.error(f"yt-dlp fetch error: {e}")
        raise RuntimeError(f"Could not load URL: {e}") from e


def search_related(title: str, uploader: str, max_results: int = 5) -> list[dict]:
    """Find loosely related tracks for autoplay."""
    clean = title.split("(")[0].split("[")[0].split("-")[0].strip()
    query = f"{uploader} {clean}"
    try:
        return search_top_tracks(query, max_results)
    except Exception:
        return []