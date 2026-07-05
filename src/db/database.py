"""
db/database.py
SQLite connection management and schema migrations.
Uses aiosqlite for async-safe access from the bot's event loop.
"""
import aiosqlite
import logging
import os

log = logging.getLogger("simvox.db")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "simvox.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id        INTEGER PRIMARY KEY,
    dj_role_id      INTEGER,
    twentyfourseven INTEGER NOT NULL DEFAULT 0,
    default_volume  INTEGER NOT NULL DEFAULT 100,
    quality         TEXT    NOT NULL DEFAULT 'high',
    sponsorblock    INTEGER NOT NULL DEFAULT 1,
    idle_timeout    INTEGER NOT NULL DEFAULT 300
);

CREATE TABLE IF NOT EXISTS queue_state (
    guild_id        INTEGER PRIMARY KEY,
    voice_channel_id INTEGER,
    text_channel_id INTEGER,
    current_track   TEXT,
    position        INTEGER NOT NULL DEFAULT 0,
    queue_json       TEXT NOT NULL DEFAULT '[]',
    loop_mode       TEXT NOT NULL DEFAULT 'off',
    volume          INTEGER NOT NULL DEFAULT 100,
    active_filter   TEXT NOT NULL DEFAULT 'none',
    autoplay        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlists (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id        INTEGER NOT NULL,
    owner_id        INTEGER NOT NULL,
    name            TEXT NOT NULL,
    tracks_json     TEXT NOT NULL DEFAULT '[]',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, owner_id, name)
);

CREATE TABLE IF NOT EXISTS play_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id        INTEGER NOT NULL,
    title           TEXT NOT NULL,
    uploader        TEXT,
    duration        INTEGER DEFAULT 0,
    requested_by    INTEGER,
    played_at       TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_history_guild ON play_history(guild_id);
CREATE INDEX IF NOT EXISTS idx_playlists_guild_owner ON playlists(guild_id, owner_id);
"""


async def init_db():
    """Create data dir + tables if they don't exist. Call once on startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()
    log.info(f"Database ready at {DB_PATH}")


def get_connection():
    """Returns a fresh aiosqlite connection. Caller must use `async with`."""
    return aiosqlite.connect(DB_PATH)