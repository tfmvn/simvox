import yt_dlp


SEARCH_CACHE = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'skip_download': True,
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

def search_audio(query: str) -> dict:
    """Scrapes the target platform for a streamable audio URL. Uses cache if available."""
    cleaned_query = query.strip().lower()
    

    if cleaned_query in SEARCH_CACHE:
        print(f"⚡ Cache Hit for query: '{query}'")
        return SEARCH_CACHE[cleaned_query]

    search_query = query if query.startswith('http') else f"ytsearch:{query}"
    

    info = ytdl.extract_info(search_query, download=False)
    

    if 'entries' in info:
        if not info['entries']:
            raise Exception("No search results found.")
        info = info['entries'][0]
        

    stream_url = info.get('url')
    if not stream_url:
        raise Exception("Could not extract raw audio stream URL.")
        
    result = {
        'source': stream_url, 
        'title': info.get('title', 'Unknown Title')
    }
    

    SEARCH_CACHE[cleaned_query] = result
    return result