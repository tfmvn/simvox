"""
db/repository.py
Typed CRUD functions over the SQLite schema. Every other module talks to
the database through here — nobody writes raw SQL outside this file.
"""
import json
import logging
from typing import Optional
from db.database import get_connection

log = logging.getLogger("simvox.db.repo")


# ── Guild Settings (DJ role, 24/7, quality, idle timeout) ───────────────────

_DEFAULT_SETTINGS = {
    "dj_role_id": None,
    "twentyfourseven": False,
    "default_volume": 100,
    "quality": "high",
    "sponsorblock": True,
    "idle_timeout": 300,
}


async def get_guild_settings(guild_id: int) -> dict:
    async with get_connection() as db:
        db.row_factory = None
        cur = await db.execute(
            "SELECT dj_role_id, twentyfourseven, default_volume, quality, sponsorblock, idle_timeout "
            "FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cur.fetchone()
        if not row:
            return dict(_DEFAULT_SETTINGS)
        return {
            "dj_role_id":       row[0],
            "twentyfourseven":  bool(row[1]),
            "default_volume":   row[2],
            "quality":          row[3],
            "sponsorblock":     bool(row[4]),
            "idle_timeout":     row[5],
        }


async def set_dj_role(guild_id: int, role_id: Optional[int]):
    await _upsert_settings(guild_id, dj_role_id=role_id)


async def set_247(guild_id: int, enabled: bool):
    await _upsert_settings(guild_id, twentyfourseven=int(enabled))


async def set_quality(guild_id: int, quality: str):
    await _upsert_settings(guild_id, quality=quality)


async def set_sponsorblock(guild_id: int, enabled: bool):
    await _upsert_settings(guild_id, sponsorblock=int(enabled))


async def set_idle_timeout(guild_id: int, seconds: int):
    await _upsert_settings(guild_id, idle_timeout=seconds)


async def _upsert_settings(guild_id: int, **fields):
    current = await get_guild_settings(guild_id)
    current.update({
        k: (int(v) if isinstance(v, bool) else v)
        for k, v in fields.items()
    })
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO guild_settings
                (guild_id, dj_role_id, twentyfourseven, default_volume, quality, sponsorblock, idle_timeout)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                dj_role_id=excluded.dj_role_id,
                twentyfourseven=excluded.twentyfourseven,
                default_volume=excluded.default_volume,
                quality=excluded.quality,
                sponsorblock=excluded.sponsorblock,
                idle_timeout=excluded.idle_timeout
            """,
            (
                guild_id,
                current["dj_role_id"],
                int(current["twentyfourseven"]),
                current["default_volume"],
                current["quality"],
                int(current["sponsorblock"]),
                current["idle_timeout"],
            ),
        )
        await db.commit()


# ── Queue Persistence ────────────────────────────────────────────────────────

async def save_queue_state(
    guild_id: int,
    voice_channel_id: Optional[int],
    text_channel_id: Optional[int],
    current_track: Optional[dict],
    position: int,
    queue: list[dict],
    loop_mode: str,
    volume: int,
    active_filter: str,
    autoplay: bool,
):
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO queue_state
                (guild_id, voice_channel_id, text_channel_id, current_track, position,
                 queue_json, loop_mode, volume, active_filter, autoplay, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                voice_channel_id=excluded.voice_channel_id,
                text_channel_id=excluded.text_channel_id,
                current_track=excluded.current_track,
                position=excluded.position,
                queue_json=excluded.queue_json,
                loop_mode=excluded.loop_mode,
                volume=excluded.volume,
                active_filter=excluded.active_filter,
                autoplay=excluded.autoplay,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                voice_channel_id,
                text_channel_id,
                json.dumps(current_track) if current_track else None,
                position,
                json.dumps(queue),
                loop_mode,
                volume,
                active_filter,
                int(autoplay),
            ),
        )
        await db.commit()


async def load_queue_state(guild_id: int) -> Optional[dict]:
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT voice_channel_id, text_channel_id, current_track, position, "
            "queue_json, loop_mode, volume, active_filter, autoplay "
            "FROM queue_state WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "voice_channel_id": row[0],
            "text_channel_id":  row[1],
            "current_track":    json.loads(row[2]) if row[2] else None,
            "position":         row[3],
            "queue":            json.loads(row[4]),
            "loop_mode":        row[5],
            "volume":           row[6],
            "active_filter":    row[7],
            "autoplay":         bool(row[8]),
        }


async def clear_queue_state(guild_id: int):
    async with get_connection() as db:
        await db.execute("DELETE FROM queue_state WHERE guild_id = ?", (guild_id,))
        await db.commit()


async def all_saved_guild_ids() -> list[int]:
    async with get_connection() as db:
        cur = await db.execute("SELECT guild_id FROM queue_state")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


# ── Playlists ────────────────────────────────────────────────────────────────

async def create_playlist(guild_id: int, owner_id: int, name: str) -> bool:
    try:
        async with get_connection() as db:
            await db.execute(
                "INSERT INTO playlists (guild_id, owner_id, name, tracks_json) VALUES (?, ?, ?, '[]')",
                (guild_id, owner_id, name),
            )
            await db.commit()
        return True
    except Exception as e:
        log.warning(f"create_playlist failed (likely duplicate): {e}")
        return False


async def save_playlist_tracks(guild_id: int, owner_id: int, name: str, tracks: list[dict]) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "UPDATE playlists SET tracks_json = ? WHERE guild_id = ? AND owner_id = ? AND name = ?",
            (json.dumps(tracks), guild_id, owner_id, name),
        )
        await db.commit()
        return cur.rowcount > 0


async def load_playlist(guild_id: int, owner_id: int, name: str) -> Optional[list[dict]]:
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT tracks_json FROM playlists WHERE guild_id = ? AND owner_id = ? AND name = ?",
            (guild_id, owner_id, name),
        )
        row = await cur.fetchone()
        return json.loads(row[0]) if row else None


async def list_playlists(guild_id: int, owner_id: int) -> list[str]:
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT name FROM playlists WHERE guild_id = ? AND owner_id = ? ORDER BY name",
            (guild_id, owner_id),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def delete_playlist(guild_id: int, owner_id: int, name: str) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "DELETE FROM playlists WHERE guild_id = ? AND owner_id = ? AND name = ?",
            (guild_id, owner_id, name),
        )
        await db.commit()
        return cur.rowcount > 0


# ── Play History / Stats ─────────────────────────────────────────────────────

async def log_play(guild_id: int, title: str, uploader: str, duration: int, requested_by: Optional[int]):
    async with get_connection() as db:
        await db.execute(
            "INSERT INTO play_history (guild_id, title, uploader, duration, requested_by) VALUES (?, ?, ?, ?, ?)",
            (guild_id, title, uploader, duration, requested_by),
        )
        await db.commit()


async def get_guild_stats(guild_id: int) -> dict:
    async with get_connection() as db:
        cur = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(duration), 0) FROM play_history WHERE guild_id = ?",
            (guild_id,),
        )
        count, total_seconds = await cur.fetchone()

        cur = await db.execute(
            "SELECT uploader, COUNT(*) c FROM play_history WHERE guild_id = ? AND uploader IS NOT NULL "
            "GROUP BY uploader ORDER BY c DESC LIMIT 1",
            (guild_id,),
        )
        top_artist_row = await cur.fetchone()

        cur = await db.execute(
            "SELECT title, COUNT(*) c FROM play_history WHERE guild_id = ? "
            "GROUP BY title ORDER BY c DESC LIMIT 1",
            (guild_id,),
        )
        top_song_row = await cur.fetchone()

        cur = await db.execute(
            "SELECT title, uploader, COUNT(*) c FROM play_history WHERE guild_id = ? "
            "GROUP BY title ORDER BY c DESC LIMIT 5",
            (guild_id,),
        )
        top5 = await cur.fetchall()

    return {
        "tracks_played": count,
        "total_seconds": total_seconds,
        "top_artist": top_artist_row[0] if top_artist_row else None,
        "top_song": top_song_row[0] if top_song_row else None,
        "top5": [{"title": r[0], "uploader": r[1], "plays": r[2]} for r in top5],
    }