# Changelog

All notable changes to Simvox are documented here. Format is loosely based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-07-06

First stable release. Everything below has been through real use in a
live server, not just written and forgotten.

### Added

- Slash-command playback: `/play`, `/playtop`, `/search`, `/nowplaying`,
  `/pause`, `/resume`, `/skip`, `/voteskip`, `/replay`, `/seek`
- Source resolution for YouTube, SoundCloud, and plain text search via
  `yt-dlp`, plus Spotify track/album/playlist links (resolved to YouTube
  audio through the optional `spotifyscraper` dependency)
- Queue management: `/queue`, `/remove`, `/move`, `/shuffle`, `/clear`,
  `/history`, with autocomplete on position-based commands
- Playlists — per-user, per-guild, persisted in SQLite (`/playlist create
  / save / load / view / list / delete`)
- Audio filters: Bass Boost, Nightcore, Vaporwave, 8D, Karaoke, Treble
- Loop modes (Off / Track / Queue) and adjustable volume (0–200)
- SponsorBlock integration — auto-skips sponsor/intro/outro segments on
  YouTube tracks, toggleable per server
- Autoplay with smarter recommendations (artist/genre-based queries, not
  just re-searching the last title) instead of leaving the queue empty
- Real, paginated lyrics via lyrics.ovh (`/lyrics`)
- Per-guild settings: DJ role, 24/7 mode, audio quality tier, SponsorBlock
  toggle, idle timeout — all configurable through `/settings` and
  `/247`/`/quality`, gated behind Manage Server
- DJ-role permission model with a built-in solo-in-voice-channel exemption
- Idle auto-disconnect after a configurable timeout, skipped entirely when
  24/7 mode is on
- Queue persistence — current track, position, queue, loop mode, volume,
  filter, and autoplay state all survive a bot restart
- Per-guild listening stats (`/stats`) — tracks played, hours played, top
  artist/song, most-played tracks
- `/help` with the full in-bot command reference

### Fixed

- `requirements.txt` was missing `aiosqlite`, which `db/database.py`
  imports unconditionally — a clean `pip install -r requirements.txt`
  would leave the bot unable to start. It's in there now.
- The README's FAQ claimed Spotify links weren't supported; that's been
  true since `core/resolver.py` added Spotify handling and just hadn't
  been corrected until this release.

### Known limitations

- Single process, no sharding — built for a handful of self-hosted
  servers, not a public bot at scale
- SponsorBlock only has data for YouTube; it can't do anything for
  SoundCloud or Spotify-resolved tracks
- Spotify support depends on scraping public pages through
  `spotifyscraper` rather than an official API, so it can break if
  Spotify changes their page structure — that's upstream, not something
  fixable here
- No automated test suite yet (tracked on the [roadmap](README.md#roadmap))

[1.0.0]: https://github.com/tfmvn/simvox/releases/tag/v1.0.0
