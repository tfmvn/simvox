import yt_dlp


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

def search_audio(query):
    """Scrapes the search query or URL for a direct audio stream."""

    search_query = query if query.startswith('http') else f"ytsearch:{query}"
    

    info = ytdl.extract_info(search_query, download=False)
    

    if 'entries' in info:
        info = info['entries'][0]
        
    return {'source': info['url'], 'title': info['title']}