import yt_dlp

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "auto",
}


def extract_stream_url(query: str):
    """
    Returns (stream_url, title) for a given YouTube URL, or for a search
    query (e.g. "never gonna give you up"), in which case the first
    matching result is used.
    """
    search_query = query if query.startswith("http") else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if "entries" in info:
            if not info["entries"]:
                raise ValueError(f"No results found for '{query}'.")
            info = info["entries"][0]
        return info["url"], info.get("title", "Unknown")