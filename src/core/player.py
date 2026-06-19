"""
core/player.py
Per-guild music state machine.
Handles queue, playback, loop, volume, filters, history, autoplay, seek.
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


class GuildMusicManager:
    def __init__(self, bot: discord.Client, guild_id: int):
        self.bot         = bot
        self.guild_id    = guild_id
        self.queue: list[dict]  = []
        self.history: list[dict] = []
        self.current: Optional[dict] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.loop_mode   = "off"
        self.volume      = 100
        self.autoplay    = False
        self.active_filter = "none"
        self._position_start: float = 0.0
        self._seek_offset:    int   = 0


        self.skip_votes: set[int] = set()


        self.np_message: Optional[discord.Message] = None
        self.text_channel: Optional[discord.TextChannel] = None


    @property
    def position(self) -> int:
        """Estimated playback position in seconds."""
        if self.voice_client and self.voice_client.is_playing():
            return self._seek_offset + int(time.monotonic() - self._position_start)
        return self._seek_offset


    async def play_next(self):
        if not self.voice_client or not self.voice_client.is_connected():
            return


        if self.loop_mode == "track" and self.current:
            next_track = self.current

        elif self.loop_mode == "queue" and self.current:
            self.queue.append(self.current)
            next_track = self.queue.pop(0) if self.queue else None
        else:
            next_track = self.queue.pop(0) if self.queue else None


        if next_track is None and self.autoplay and self.current:
            try:
                from core.scraper import search_related
                related = await asyncio.to_thread(
                    search_related, self.current["title"], self.current.get("uploader", "")
                )

                candidates = [t for t in related if t["title"] != self.current["title"]]
                if candidates:
                    next_track = candidates[0]
                    log.info(f"Autoplay queued: {next_track['title']}")
            except Exception as e:
                log.warning(f"Autoplay fetch failed: {e}")

        if next_track is None:
            self.current = None
            self._seek_offset = 0
            if self.text_channel:
                try:
                    await self.text_channel.send(
                        embed=_queue_empty_embed(), delete_after=30
                    )
                except Exception:
                    pass
            return

        if self.current and self.loop_mode != "track":
            self.history.append(self.current)
            if len(self.history) > 50:
                self.history.pop(0)

        self.current = next_track
        self.skip_votes.clear()
        self._seek_offset = 0
        self._position_start = time.monotonic()

        await self._start_stream(next_track)

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
            asyncio.run_coroutine_threadsafe(
                self._update_np_message(), self.bot.loop
            )

    async def _update_np_message(self):
        from utils.embeds import now_playing
        from ui.views   import NowPlayingView
        if not self.current:
            return
        embed = now_playing(self.current, self.position)
        view  = NowPlayingView(self)
        try:
            if self.np_message:
                await self.np_message.edit(embed=embed, view=view)
        except Exception:
            pass


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

    async def disconnect(self):
        self.queue.clear()
        self.current = None
        self.skip_votes.clear()
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
        self.voice_client = None


def _queue_empty_embed() -> discord.Embed:
    from utils.embeds import info_embed
    return info_embed("Queue Empty", "No more tracks — use `/play` to add more.")

