"""
core/player.py
Owns per-guild playback state — the queue, the currently playing track,
volume, and loop mode — and drives the play/advance loop. Commands call
into this instead of touching FFmpeg or state dicts directly.
"""
import asyncio
import logging
from typing import Awaitable, Callable, Optional

import discord

from utils.helpers import extract_stream_url
from utils.queue import QueueManager, Track

log = logging.getLogger("simvox.player")

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

Announce = Callable[[str], Awaitable[None]]


class PlayerManager:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.queues = QueueManager()
        self._volumes: dict[int, int] = {}
        self._loop_enabled: dict[int, bool] = {}
        self._current: dict[int, Track] = {}

    # ── Volume ───────────────────────────────────────────────────────────

    def get_volume(self, guild_id: int) -> int:
        return self._volumes.setdefault(guild_id, 100)

    def set_volume(self, guild_id: int, level: int, voice_client: Optional[discord.VoiceClient]) -> None:
        self._volumes[guild_id] = level
        if voice_client and voice_client.source:
            voice_client.source.volume = level / 100

    # ── Loop ─────────────────────────────────────────────────────────────

    def toggle_loop(self, guild_id: int) -> bool:
        enabled = not self._loop_enabled.get(guild_id, False)
        self._loop_enabled[guild_id] = enabled
        return enabled

    # ── Current track / queueing ─────────────────────────────────────────

    def now_playing(self, guild_id: int) -> Optional[Track]:
        return self._current.get(guild_id)

    def enqueue(self, guild_id: int, url: str, title: str) -> None:
        self.queues.add(guild_id, url, title)

    # ── Lifecycle ────────────────────────────────────────────────────────

    def reset(self, guild_id: int) -> None:
        """Clears queue, current track, and loop mode for a guild."""
        self.queues.clear(guild_id)
        self._current.pop(guild_id, None)
        self._loop_enabled[guild_id] = False
        log.info(f"Playback state reset for guild {guild_id}.")

    async def play_next(self, voice_client: discord.VoiceClient, guild_id: int, announce: Announce) -> None:
        """
        Advances playback for a guild: replays the current track if
        looping, otherwise pulls the next one off the queue. Tracks that
        fail to extract or play are skipped in a loop rather than via
        recursion, so a bad run of tracks can't blow the call stack.
        """
        while True:
            if not voice_client or not voice_client.is_connected():
                return

            if self._loop_enabled.get(guild_id) and guild_id in self._current:
                track = self._current[guild_id]
            else:
                track = self.queues.pop_next(guild_id)
                if track is None:
                    self._current.pop(guild_id, None)
                    return
                self._current[guild_id] = track

            try:
                stream_url, title = extract_stream_url(track.url)
            except Exception as e:
                log.warning(f"Extraction failed for '{track.title}': {e}")
                await announce(f"Could not load {track.title}, skipping.")
                self._current.pop(guild_id, None)
                continue

            def after_playing(error, guild_id=guild_id, voice_client=voice_client, announce=announce):
                if error:
                    log.error(f"Playback error in guild {guild_id}: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.play_next(voice_client, guild_id, announce), self.bot.loop
                )

            try:
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
                    volume=self.get_volume(guild_id) / 100,
                )
                voice_client.play(source, after=after_playing)
            except Exception as e:
                log.error(f"FFmpeg failed to start for '{title}': {e}")
                await announce(f"Playback failed for {title}, skipping.")
                self._current.pop(guild_id, None)
                continue

            log.info(f"Guild {guild_id}: now playing '{title}'.")
            await announce(f"Now playing: {title}")
            return