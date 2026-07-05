"""
utils/embeds.py
All embed builders for Simvox. Red-accent house style.
"""
import discord
from typing import Optional

# ── Palette ────────────────────────────────────────────────────────────────
RED        = 0xE8132A   # primary accent
RED_DARK   = 0x8B0000   # deeper red for errors
DARK       = 0x0A0A0F   # void background
GOLD       = 0xFFD700   # highlights (queue positions etc.)
GREY       = 0x2B2D31   # neutral fields

SIMVOX_ICON = "https://i.imgur.com/placeholder.png"   # swap for real icon


def _base(color: int = RED) -> discord.Embed:
    e = discord.Embed(color=color)
    e.set_footer(text="SIMVOX", icon_url=SIMVOX_ICON)
    return e


def now_playing(track: dict, position: int = 0, requester: Optional[discord.Member] = None, manager=None) -> discord.Embed:
    dur   = track.get("duration", 0) or 0
    pos   = min(position, dur)
    pct   = (pos / dur) if dur else 0
    bar   = _progress_bar(pct)
    elapsed = _fmt_time(pos)
    total   = _fmt_time(dur)

    e = _base(RED)
    e.title = "▶  NOW PLAYING"
    e.description = f"### [{track['title']}]({track.get('webpage_url', '')})"
    e.add_field(name="", value=f"`{elapsed}` {bar} `{total}`", inline=False)
    e.add_field(name="🎤 Artist",    value=track.get("uploader", "Unknown"),   inline=True)
    e.add_field(name="⏱ Duration",  value=total,                               inline=True)

    if track.get("view_count"):
        e.add_field(name="👁 Views", value=f"{track['view_count']:,}", inline=True)
    if track.get("like_count"):
        e.add_field(name="👍 Likes", value=f"{track['like_count']:,}", inline=True)
    if track.get("upload_date"):
        e.add_field(name="📅 Uploaded", value=_fmt_upload_date(track["upload_date"]), inline=True)

    if requester:
        e.add_field(name="👤 Requested by", value=requester.mention, inline=True)
    elif track.get("requested_by_name"):
        e.add_field(name="👤 Requested by", value=track["requested_by_name"], inline=True)

    if manager is not None:
        loop_str   = {"off": "Off", "track": "🔂 Track", "queue": "🔁 Queue"}.get(manager.loop_mode, "Off")
        filter_str = "Off" if manager.active_filter == "none" else manager.active_filter.title()
        e.add_field(name="🔁 Loop",   value=loop_str,                  inline=True)
        e.add_field(name="🎛 Filter", value=filter_str,                inline=True)
        e.add_field(name="🔊 Volume", value=f"{manager.volume}%",      inline=True)

    if track.get("thumbnail"):
        e.set_thumbnail(url=track["thumbnail"])
    return e


def autoplay_embed(previous_track: dict, recommendations: list) -> discord.Embed:
    e = _base(RED)
    e.title = "🤖  Autoplay"
    e.description = f"Because you listened to **{previous_track['title']}**:"
    lines = [f"`{i}.` {t['title']}" for i, t in enumerate(recommendations, 1)]
    e.add_field(name="Queued up", value="\n".join(lines) or "Nothing found.", inline=False)
    return e


def queue_embed(manager, page: int = 0) -> discord.Embed:
    per_page = 10
    q        = manager.queue
    total    = len(q)
    start    = page * per_page
    end      = start + per_page
    chunk    = q[start:end]

    e = _base(RED)
    e.title = "📋  QUEUE"

    if manager.current:
        dur_str = _fmt_time(manager.current.get("duration", 0))
        remaining = max(0, (manager.current.get("duration", 0) or 0) - manager.position)
        e.add_field(
            name="▶ Now Playing",
            value=f"[{manager.current['title']}]({manager.current.get('webpage_url','')}) `{dur_str}` • ends in `{_fmt_time(remaining)}`",
            inline=False,
        )
    else:
        e.description = "Queue is empty — use `/play` to load something up."
        return e

    if chunk:
        lines = []
        for i, t in enumerate(chunk, start=start + 1):
            dur_str = _fmt_time(t.get("duration", 0))
            eta_str = _fmt_time(manager.eta_for_queue_index(i - 1))
            lines.append(f"`{i:02}.` **{t['title']}** `{dur_str}` — plays in `{eta_str}`")
        e.add_field(name=f"Up Next  [{start+1}–{min(end,total)} of {total}]",
                    value="\n".join(lines), inline=False)
    else:
        e.add_field(name="Up Next", value="Nothing queued.", inline=False)

    total_dur = sum(t.get("duration", 0) or 0 for t in q)
    loop_str  = {"off": "Off", "track": "🔂 Track", "queue": "🔁 Queue"}.get(manager.loop_mode, "Off")
    e.set_footer(text=f"SIMVOX  •  Total: {_fmt_time(total_dur)}  •  Loop: {loop_str}  •  Page {page+1}/{max(1,(total-1)//per_page+1)}")
    return e


def search_results(query: str, tracks: list) -> discord.Embed:
    e = _base(RED)
    e.title = f"🔍  Search: {query[:50]}"
    e.description = "Pick a track from the dropdown below."
    for i, t in enumerate(tracks[:10], 1):
        dur = _fmt_time(t.get("duration", 0))
        e.add_field(
            name=f"{i}. {t['title'][:60]}",
            value=f"🎤 {t.get('uploader','?')}  •  ⏱ {dur}",
            inline=False,
        )
    return e


def track_added(track: dict, position: int, eta_seconds: Optional[int] = None) -> discord.Embed:
    e = _base(RED)
    e.title = "➕  Added to Queue"
    e.description = f"[{track['title']}]({track.get('webpage_url','')})"
    e.add_field(name="Position",  value=f"`#{position}`",                inline=True)
    e.add_field(name="Duration",  value=_fmt_time(track.get("duration",0)), inline=True)
    e.add_field(name="Artist",    value=track.get("uploader","?"),       inline=True)
    if eta_seconds is not None:
        e.add_field(name="Plays in", value=f"`{_fmt_time(eta_seconds)}`", inline=True)
    if track.get("thumbnail"):
        e.set_thumbnail(url=track["thumbnail"])
    return e


def error_embed(message: str) -> discord.Embed:
    e = _base(RED_DARK)
    e.title = "❌  Error"
    e.description = message
    return e


def success_embed(message: str) -> discord.Embed:
    e = _base(RED)
    e.title = "✅  Done"
    e.description = message
    return e


def info_embed(title: str, message: str) -> discord.Embed:
    e = _base(GREY)
    e.title = title
    e.description = message
    return e


def history_embed(history: list) -> discord.Embed:
    e = _base(RED)
    e.title = "📜  Play History"
    if not history:
        e.description = "Nothing played yet this session."
        return e
    lines = []
    for i, t in enumerate(reversed(history[-15:]), 1):
        dur = _fmt_time(t.get("duration", 0))
        lines.append(f"`{i:02}.` {t['title'][:55]} `{dur}`")
    e.description = "\n".join(lines)
    return e


def filters_embed(active_filter: str) -> discord.Embed:
    e = _base(RED)
    e.title = "🎛  Audio Filters"
    filters = {
        "none":       ("Off",         "No processing applied."),
        "bassboost":  ("Bass Boost",  "Heavy low-end enhancement."),
        "nightcore":  ("Nightcore",   "Pitched up, sped up."),
        "vaporwave":  ("Vaporwave",   "Slowed, pitched down."),
        "8d":         ("8D Audio",    "Panning stereo effect."),
        "karaoke":    ("Karaoke",     "Vocal removal attempt."),
        "treble":     ("Treble Boost","High-end clarity boost."),
    }
    lines = []
    for key, (label, desc) in filters.items():
        mark = "▶" if key == active_filter else "·"
        lines.append(f"`{mark}` **{label}** — {desc}")
    e.description = "\n".join(lines)
    return e


def volume_embed(vol: int) -> discord.Embed:
    e = _base(RED)
    e.title = "🔊  Volume"
    bar = _volume_bar(vol)
    e.description = f"{bar}  **{vol}%**"
    return e


def quality_embed(active: str) -> discord.Embed:
    e = _base(RED)
    e.title = "🎚  Audio Quality"
    tiers = {
        "low":    "Lowest bitrate — best for slow/limited VPS bandwidth.",
        "medium": "≤96kbps — balanced.",
        "high":   "≤192kbps — recommended default.",
        "source": "Whatever the source provides, uncapped.",
    }
    lines = []
    for key, desc in tiers.items():
        mark = "▶" if key == active else "·"
        lines.append(f"`{mark}` **{key.title()}** — {desc}")
    e.description = "\n".join(lines)
    return e


def settings_embed(settings: dict, dj_role: Optional[discord.Role] = None) -> discord.Embed:
    e = _base(RED)
    e.title = "⚙️  Server Settings"
    e.add_field(name="DJ Role", value=dj_role.mention if dj_role else "Not set (anyone can control)", inline=False)
    e.add_field(name="24/7 Mode", value="🟢 On" if settings["twentyfourseven"] else "🔴 Off", inline=True)
    e.add_field(name="SponsorBlock", value="🟢 On" if settings["sponsorblock"] else "🔴 Off", inline=True)
    e.add_field(name="Idle Timeout", value=f"{settings['idle_timeout']//60} min", inline=True)
    e.add_field(name="Quality", value=settings["quality"].title(), inline=True)
    return e


def stats_embed(guild_name: str, stats: dict) -> discord.Embed:
    e = _base(RED)
    e.title = f"📊  Music Stats — {guild_name}"
    hours = stats["total_seconds"] / 3600
    e.add_field(name="Tracks Played", value=f"{stats['tracks_played']:,}", inline=True)
    e.add_field(name="Hours Played",  value=f"{hours:,.1f}", inline=True)
    e.add_field(name="Top Artist",    value=stats["top_artist"] or "—", inline=True)
    e.add_field(name="Top Song",      value=stats["top_song"] or "—", inline=True)
    if stats["top5"]:
        lines = [f"`{i}.` {t['title'][:50]} — {t['plays']}x" for i, t in enumerate(stats["top5"], 1)]
        e.add_field(name="Most Played", value="\n".join(lines), inline=False)
    return e


def playlist_embed(name: str, tracks: list) -> discord.Embed:
    e = _base(RED)
    e.title = f"🎵  Playlist: {name}"
    if not tracks:
        e.description = "Empty playlist."
        return e
    total_dur = sum(t.get("duration", 0) or 0 for t in tracks)
    lines = [f"`{i:02}.` {t['title'][:55]} `{_fmt_time(t.get('duration',0))}`" for i, t in enumerate(tracks[:15], 1)]
    if len(tracks) > 15:
        lines.append(f"...and {len(tracks)-15} more.")
    e.description = "\n".join(lines)
    e.set_footer(text=f"SIMVOX  •  {len(tracks)} tracks  •  {_fmt_time(total_dur)} total")
    return e


def playlist_list_embed(names: list) -> discord.Embed:
    e = _base(RED)
    e.title = "📂  Your Playlists"
    if not names:
        e.description = "No playlists yet. Use `/playlist create` to make one."
        return e
    e.description = "\n".join(f"• {n}" for n in names)
    return e


def lyrics_embed(title: str, lyrics: str, page: int, total_pages: int) -> discord.Embed:
    e = _base(RED)
    e.title = f"🎤  {title[:80]}"
    e.description = lyrics
    e.set_footer(text=f"SIMVOX  •  Page {page+1}/{total_pages}")
    return e


# ── Helpers ─────────────────────────────────────────────────────────────────
def _fmt_time(seconds: int) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def _fmt_upload_date(yyyymmdd: str) -> str:
    try:
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
    except Exception:
        return yyyymmdd


def _progress_bar(pct: float, length: int = 18) -> str:
    filled = int(pct * length)
    bar    = "█" * filled + "▒" * (length - filled)
    return f"[{bar}]"


def _volume_bar(vol: int, length: int = 16) -> str:
    filled = int((min(vol, 200) / 200) * length)
    return "▮" * filled + "▯" * (length - filled)