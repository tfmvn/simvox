"""
core/idle.py
Tracks per-guild idle state and disconnects the bot from voice after a
configurable timeout when nothing is playing — unless 24/7 mode is on.

"Idle" = voice client connected but not playing and not paused (i.e. the
queue ran out), OR the bot is alone in the voice channel.
"""
import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.player import GuildMusicManager

log = logging.getLogger("simvox.idle")

DEFAULT_TIMEOUT = 300  # 5 minutes, overridden by guild_settings.idle_timeout


class IdleTracker:
    """One instance shared by the bot; manages a timer task per guild."""

    def __init__(self, bot):
        self.bot = bot
        self._tasks: dict[int, asyncio.Task] = {}

    def notify_activity(self, guild_id: int):
        """Call whenever playback starts/resumes — cancels any pending disconnect."""
        task = self._tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    def schedule_check(self, manager: "GuildMusicManager", timeout: int = DEFAULT_TIMEOUT):
        """Call whenever the queue empties or playback stops — starts the countdown."""
        guild_id = manager.guild_id
        self.notify_activity(guild_id)  # cancel any existing timer first
        task = asyncio.create_task(self._countdown(manager, timeout))
        self._tasks[guild_id] = task

    async def _countdown(self, manager: "GuildMusicManager", timeout: int):
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return

        try:
            from db import repository as repo
            settings = await repo.get_guild_settings(manager.guild_id)
            if settings["twentyfourseven"]:
                log.info(f"Guild {manager.guild_id} idle but 24/7 is on — staying connected.")
                return

            vc = manager.voice_client
            if not vc or not vc.is_connected():
                return

            # Double-check it's actually still idle (nothing started in the meantime)
            if vc.is_playing() or vc.is_paused():
                return

            log.info(f"Guild {manager.guild_id} idle for {timeout}s — disconnecting.")
            try:
                if manager.text_channel:
                    from utils.embeds import info_embed
                    await manager.text_channel.send(
                        embed=info_embed("👋  Leaving", f"No activity for {timeout//60} minutes — disconnecting to free up resources."),
                        delete_after=30,
                    )
            except Exception:
                pass

            await manager.disconnect()
        finally:
            # Always release our slot when the countdown finishes — whether
            # it disconnected, bailed out early, or hit an error — so a
            # finished task doesn't linger in _tasks until overwritten.
            self._tasks.pop(manager.guild_id, None)

    def cancel_all(self):
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()