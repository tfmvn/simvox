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

def search_top_tracks(query: str, max_results: int = 10) -> list:
    """Scrapes the platform and returns a list of up to 10 track matches."""
    search_query = query if query.startswith('http') else f"ytsearch{max_results}:{query}"
    

    info = ytdl.extract_info(search_query, download=False)
    
    tracks = []
    

    if 'entries' in info:
        for entry in info['entries']:
            if entry:
                tracks.append({
                    'source': entry['url'],
                    'title': entry['title'],
                    'duration': entry.get('duration', 0)
                })
    else:

        tracks.append({
            'source': info['url'],
            'title': info.get('title', 'Unknown Title'),
            'duration': info.get('duration', 0)
        })
        
    if not tracks:
        raise Exception("No results found for your query.")
        
    return tracks