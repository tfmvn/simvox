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


def now_playing(track: dict, position: int = 0, requester: Optional[discord.Member] = None) -> discord.Embed:
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
    if requester:
        e.add_field(name="👤 Requested by", value=requester.mention,           inline=True)
    if track.get("thumbnail"):
        e.set_thumbnail(url=track["thumbnail"])
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
        e.add_field(
            name="▶ Now Playing",
            value=f"[{manager.current['title']}]({manager.current.get('webpage_url','')}) `{dur_str}`",
            inline=False,
        )
    else:
        e.description = "Queue is empty — use `/play` to load something up."
        return e

    if chunk:
        lines = []
        for i, t in enumerate(chunk, start=start + 1):
            dur_str = _fmt_time(t.get("duration", 0))
            lines.append(f"`{i:02}.` **{t['title']}** `{dur_str}`")
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


def track_added(track: dict, position: int) -> discord.Embed:
    e = _base(RED)
    e.title = "➕  Added to Queue"
    e.description = f"[{track['title']}]({track.get('webpage_url','')})"
    e.add_field(name="Position",  value=f"`#{position}`",                inline=True)
    e.add_field(name="Duration",  value=_fmt_time(track.get("duration",0)), inline=True)
    e.add_field(name="Artist",    value=track.get("uploader","?"),       inline=True)
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


# ── Helpers ─────────────────────────────────────────────────────────────────
def _fmt_time(seconds: int) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def _progress_bar(pct: float, length: int = 18) -> str:
    filled = int(pct * length)
    bar    = "█" * filled + "▒" * (length - filled)
    return f"[{bar}]"


def _volume_bar(vol: int, length: int = 16) -> str:
    filled = int((min(vol, 200) / 200) * length)
    return "▮" * filled + "▯" * (length - filled)

