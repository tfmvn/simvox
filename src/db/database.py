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


async def init_db() -> None:
    """
    Create the data dir + tables if they don't already exist.
    Call this once on startup, before anything touches the db.
    Safe to call on every boot since it's all CREATE TABLE IF NOT EXISTS.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()
    log.info(f"Database ready at {DB_PATH}")


def get_connection() -> aiosqlite.Connection:
    """
    Returns a brand new aiosqlite connection — not a shared/pooled one.
    Every call opens its own connection, so always use it as
    `async with get_connection() as db:` and don't hang onto it.
    This keeps things simple and avoids cross-coroutine locking issues,
    at the cost of a connect/close per query — fine for a bot this size.
    """
    return aiosqlite.connect(DB_PATH)