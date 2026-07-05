"""
spotify_test.py
Fetch a Spotify playlist and save it as JSON in the same directory.
Usage: python spotify_test.py <spotify_playlist_url>
"""
import json
import sys
import re
import os
from pathlib import Path

try:
    from spotify_scraper import SpotifyClient
except ImportError:
    print("ERROR: Run `pip install spotifyscraper` first.")
    sys.exit(1)

_ID_RE = re.compile(r"open\.spotify\.com/(?:intl-[a-z]+/)?(?:embed/)?playlist/([A-Za-z0-9]+)", re.IGNORECASE)


def get_playlist_id(url: str) -> str:
    match = _ID_RE.search(url)
    if not match:
        print(f"ERROR: Couldn't parse playlist ID from: {url}")
        sys.exit(1)
    return match.group(1)


def fetch_playlist(url: str) -> dict:
    playlist_id = get_playlist_id(url)
    print(f"Fetching playlist ID: {playlist_id}")

    with SpotifyClient() as client:
        playlist = client.get_playlist(playlist_id)

    tracks = []
    for item in playlist.tracks:
        track = getattr(item, "track", item)
        if not track or not getattr(track, "name", None):
            continue

        artists = getattr(track, "artists", [])
        artist_names = [a.name for a in artists] if artists else []

        tracks.append({
            "name":        track.name,
            "artists":     artist_names,
            "duration_ms": getattr(track, "duration_ms", 0),
            "id":          getattr(track, "id", None),
            "preview_url": getattr(track, "preview_url", None),
        })

    return {
        "id":          getattr(playlist, "id", playlist_id),
        "name":        getattr(playlist, "name", "Unknown Playlist"),
        "description": getattr(playlist, "description", ""),
        "owner":       getattr(getattr(playlist, "owner", None), "display_name", None),
        "total_tracks": len(tracks),
        "tracks":      tracks,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python spotify_test.py <spotify_playlist_url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"URL: {url}")

    data = fetch_playlist(url)
    print(f"Got {data['total_tracks']} tracks from \"{data['name']}\"")

    out_path = Path(__file__).parent / f"playlist_{data['id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()