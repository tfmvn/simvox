"""
core/player.py
Per-guild music state machine.
Handles queue, playback, loop, volume, filters, history, autoplay, seek,
SponsorBlock segment skipping, quality selection, live progress updates,
idle-disconnect hooks, and SQLite persistence.
"""
import discord
import asyncio
import time
import random
import logging
from typing import Optional

log = logging.getLogger("simvox.player")

AUDIO_FILTERS = {
    "none":      "",
    "bassboost": "bass=g=20,dynaudnorm=f=200",
    "nightcore": "aresample=48000,asetrate=48000*1.25",
    "vaporwave": "aresample=48000,asetrate=48000*0.8",
    "8d":        "apulsator=hz=0.08",
    "karaoke":   "pan=stereo|c0=c0-c1|c1=c1-c0",
    "treble":    "treble=g=10",
}

PROGRESS_UPDATE_INTERVAL = 10  # seconds between live now-playing edits


class GuildMusicManager:
    def __init__(self, bot: discord.Client, guild_id: int):
        self.bot         = bot
        self.guild_id    = guild_id
        self.queue: list[dict]   = []
        self.history: list[dict] = []
        self.current: Optional[dict] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.loop_mode   = "off"
        self.volume      = 100
        self.autoplay    = False
        self.active_filter = "none"
        self.quality     = "high"
        self._position_start: float = 0.0
        self._seek_offset:    int   = 0

        self.skip_votes: set[int] = set()

        self.np_message: Optional[discord.Message] = None
        self.text_channel: Optional[discord.TextChannel] = None

        # SponsorBlock state for the current track
        self._sb_segments: list[dict] = []
        self._sb_task: Optional[asyncio.Task] = None

        # Live progress-update loop
        self._progress_task: Optional[asyncio.Task] = None

        # Idle tracker reference, set by the cog on creation
        self.idle_tracker = None

    # ── Public state ────────────────────────────────────────────────────────

    @property
    def position(self) -> int:
        """Estimated playback position in seconds."""
        if self.voice_client and self.voice_client.is_playing():
            return self._seek_offset + int(time.monotonic() - self._position_start)
        return self._seek_offset

    def eta_for_queue_index(self, index: int) -> int:
        """
        Seconds until the track at `index` (0-based, within self.queue)
        starts playing, accounting for remaining time on the current track
        and full duration of everything ahead of it in queue.
        """
        eta = 0
        if self.current:
            remaining = max(0, (self.current.get("duration", 0) or 0) - self.position)
            eta += remaining
        for t in self.queue[:index]:
            eta += t.get("duration", 0) or 0
        return eta

    # ── Playback ─────────────────────────────────────────────────────────────

    async def play_next(self):
        if not self.voice_client or not self.voice_client.is_connected():
            return

        self._stop_sb_watcher()
        self._stop_progress_loop()

        if self.loop_mode == "track" and self.current:
            next_track = self.current
        elif self.loop_mode == "queue" and self.current:
            self.queue.append(self.current)
            next_track = self.queue.pop(0) if self.queue else None
        else:
            next_track = self.queue.pop(0) if self.queue else None

        # Autoplay — smarter recommendations instead of raw title search
        if next_track is None and self.autoplay and self.current:
            try:
                from core.recommend import get_recommendations
                candidates = await get_recommendations(self.current, self.history, max_results=3)
                if candidates:
                    next_track = candidates[0]
                    self.queue.extend(candidates[1:])  # queue up the rest too
                    log.info(f"Autoplay queued: {next_track['title']}")
                    if self.text_channel:
                        from utils.embeds import autoplay_embed
                        try:
                            await self.text_channel.send(embed=autoplay_embed(self.current, candidates))
                        except Exception:
                            pass
            except Exception as e:
                log.warning(f"Autoplay fetch failed: {e}")

        if next_track is None:
            self.current = None
            self._seek_offset = 0
            await self._persist_state()
            if self.idle_tracker:
                self.idle_tracker.schedule_check(self)
            if self.text_channel:
                try:
                    await self.text_channel.send(embed=_queue_empty_embed(), delete_after=30)
                except Exception:
                    pass
            return

        if self.current and self.loop_mode != "track":
            self.history.append(self.current)
            if len(self.history) > 50:
                self.history.pop(0)
            # Log to persistent history for /stats
            try:
                from db import repository as repo
                await repo.log_play(
                    self.guild_id,
                    self.current.get("title", "Unknown"),
                    self.current.get("uploader", "Unknown"),
                    self.current.get("duration", 0) or 0,
                    self.current.get("requested_by"),
                )
            except Exception as e:
                log.warning(f"History log failed: {e}")

        self.current = next_track
        self.skip_votes.clear()
        self._seek_offset = 0
        self._position_start = time.monotonic()

        if self.idle_tracker:
            self.idle_tracker.notify_activity(self.guild_id)

        await self._start_stream(next_track)
        await self._persist_state()

    async def _start_stream(self, track: dict, seek: int = 0):
        """Build FFmpeg source and start playing."""
        self._seek_offset = seek
        self._position_start = time.monotonic()

        af = AUDIO_FILTERS.get(self.active_filter, "")
        vol_filter = f"volume={self.volume/100:.2f}"
        combined = ",".join(filter(None, [af, vol_filter]))

        ffmpeg_opts = {
            "before_options": (
                "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                + (f" -ss {seek}" if seek else "")
            ),
            "options": f"-vn -af {combined}" if combined else "-vn",
        }

        source = discord.FFmpegPCMAudio(track["source"], **ffmpeg_opts)

        def _after(error):
            if error:
                log.error(f"Player error [{self.guild_id}]: {error}")
            asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)

        if self.voice_client.is_playing():
            self.voice_client.stop()

        self.voice_client.play(source, after=_after)

        if self.text_channel:
            asyncio.run_coroutine_threadsafe(self._update_np_message(), self.bot.loop)

        self._start_progress_loop()
        await self._start_sb_watcher(track, seek)

    async def _update_np_message(self):
        from utils.embeds import now_playing
        from ui.views   import NowPlayingView
        if not self.current:
            return
        embed = now_playing(self.current, self.position, manager=self)
        view  = NowPlayingView(self)
        try:
            if self.np_message:
                await self.np_message.edit(embed=embed, view=view)
        except Exception:
            pass

    # ── Live progress updates ────────────────────────────────────────────────

    def _start_progress_loop(self):
        self._stop_progress_loop()
        self._progress_task = asyncio.create_task(self._progress_loop())

    def _stop_progress_loop(self):
        if self._progress_task and not self._progress_task.done():
            self._progress_task.cancel()
        self._progress_task = None

    async def _progress_loop(self):
        try:
            while True:
                await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)
                if not self.voice_client or not self.voice_client.is_playing():
                    continue
                if not self.np_message:
                    continue
                await self._update_np_message()
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.warning(f"Progress loop error: {e}")

    # ── SponsorBlock ─────────────────────────────────────────────────────────

    async def _start_sb_watcher(self, track: dict, seek: int):
        self._sb_segments = []
        try:
            from db import repository as repo
            settings = await repo.get_guild_settings(self.guild_id)
            if not settings.get("sponsorblock", True):
                return
        except Exception:
            pass

        from core.sponsorblock import extract_video_id, get_segments
        video_id = extract_video_id(track.get("webpage_url", ""))
        if not video_id:
            return

        segments = await get_segments(video_id)
        if not segments:
            return

        self._sb_segments = segments
        self._sb_task = asyncio.create_task(self._sb_watch_loop(seek))

    def _stop_sb_watcher(self):
        if self._sb_task and not self._sb_task.done():
            self._sb_task.cancel()
        self._sb_task = None
        self._sb_segments = []

    async def _sb_watch_loop(self, start_pos: int):
        """Polls playback position and seeks past any sponsor segment it enters."""
        from core.sponsorblock import segment_containing
        try:
            current = segment_containing(self._sb_segments, start_pos)
            if current:
                await self._skip_segment(current)

            while True:
                await asyncio.sleep(1)
                if not self.voice_client or not self.voice_client.is_playing():
                    continue
                pos = self.position
                seg = segment_containing(self._sb_segments, pos)
                if seg:
                    await self._skip_segment(seg)
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.warning(f"SponsorBlock watcher error: {e}")

    async def _skip_segment(self, segment: dict):
        target = int(segment["end"]) + 1
        log.info(f"SponsorBlock: skipping {segment['category']} segment to {target}s")
        await self._start_stream(self.current, seek=target)

    # ── Persistence ──────────────────────────────────────────────────────────

    async def _persist_state(self):
        try:
            from db import repository as repo
            await repo.save_queue_state(
                guild_id=self.guild_id,
                voice_channel_id=self.voice_client.channel.id if self.voice_client else None,
                text_channel_id=self.text_channel.id if self.text_channel else None,
                current_track=self.current,
                position=self.position,
                queue=self.queue,
                loop_mode=self.loop_mode,
                volume=self.volume,
                active_filter=self.active_filter,
                autoplay=self.autoplay,
            )
        except Exception as e:
            log.warning(f"Persist state failed: {e}")

    async def restore_state(self, state: dict):
        """Apply a loaded queue_state row to this manager (does not start playback)."""
        self.queue        = state["queue"]
        self.loop_mode     = state["loop_mode"]
        self.volume        = state["volume"]
        self.active_filter = state["active_filter"]
        self.autoplay      = state["autoplay"]
        if state["current_track"]:
            self.queue.insert(0, state["current_track"])

    # ── Controls ─────────────────────────────────────────────────────────────

    def add_to_queue(self, track: dict):
        self.queue.append(track)

    def skip(self):
        self.skip_votes.clear()
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
            return True
        return False

    def pause(self) -> bool:
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            return True
        return False

    def resume(self) -> bool:
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            if self.idle_tracker:
                self.idle_tracker.notify_activity(self.guild_id)
            return True
        return False

    def set_volume(self, vol: int):
        self.volume = max(0, min(200, vol))

    def set_loop(self, mode: str):
        if mode in ("off", "track", "queue"):
            self.loop_mode = mode

    def shuffle(self):
        random.shuffle(self.queue)

    def remove(self, index: int) -> Optional[dict]:
        """Remove track at 1-based index. Returns removed track or None."""
        idx = index - 1
        if 0 <= idx < len(self.queue):
            return self.queue.pop(idx)
        return None

    def move(self, from_pos: int, to_pos: int) -> bool:
        """Move track from 1-based from_pos to 1-based to_pos."""
        fi, ti = from_pos - 1, to_pos - 1
        if 0 <= fi < len(self.queue) and 0 <= ti < len(self.queue):
            track = self.queue.pop(fi)
            self.queue.insert(ti, track)
            return True
        return False

    def clear_queue(self):
        self.queue.clear()
        self.skip_votes.clear()

    async def seek(self, seconds: int):
        """Seek to absolute position in seconds."""
        if not self.current or not self.voice_client:
            return False
        await self._start_stream(self.current, seek=seconds)
        return True

    async def replay(self):
        """Restart current track from beginning."""
        if not self.current:
            return False
        await self._start_stream(self.current, seek=0)
        return True

    def set_filter(self, filter_name: str) -> bool:
        if filter_name not in AUDIO_FILTERS:
            return False
        self.active_filter = filter_name
        return True

    async def apply_filter(self, filter_name: str) -> bool:
        """Change filter and restart stream at current position."""
        if not self.set_filter(filter_name):
            return False
        if self.current and self.voice_client and (
            self.voice_client.is_playing() or self.voice_client.is_paused()
        ):
            pos = self.position
            await self._start_stream(self.current, seek=pos)
        return True

    def set_quality(self, quality: str) -> bool:
        from core.scraper import QUALITY_FORMATS
        if quality not in QUALITY_FORMATS:
            return False
        self.quality = quality
        return True

    async def disconnect(self):
        self._stop_sb_watcher()
        self._stop_progress_loop()
        self.queue.clear()
        self.current = None
        self.skip_votes.clear()
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
        self.voice_client = None
        try:
            from db import repository as repo
            await repo.clear_queue_state(self.guild_id)
        except Exception:
            pass


def _queue_empty_embed() -> discord.Embed:
    from utils.embeds import info_embed
    return info_embed("Queue Empty", "No more tracks — use `/play` to add more.")