import discord
from discord.ext import commands
import asyncio
import logging

from utils.helpers import extract_stream_url
from utils.queue import QueueManager

log = logging.getLogger("simvox.music")

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = QueueManager()
        self.volumes: dict[int, int] = {}

    def get_volume(self, guild_id: int) -> int:
        return self.volumes.setdefault(guild_id, 100)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # The bot itself got disconnected (kicked, moved out, connection drop, etc.)
        if member.id == self.bot.user.id and after.channel is None:
            self.queues.clear(member.guild.id)
            log.info(f"Bot left voice in {member.guild.name} — queue cleared.")
            return

        # Everyone else left the channel the bot is in — leave and clean up.
        vc = member.guild.voice_client
        if vc and vc.channel and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()
            self.queues.clear(member.guild.id)
            log.info(f"Left {member.guild.name} — voice channel was empty.")

    @commands.command()
    async def join(self, ctx: commands.Context) -> None:
        if not ctx.author.voice:
            await ctx.send("You're not in a voice channel.")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(f"Joined {channel.name}.")

    @commands.command()
    async def leave(self, ctx: commands.Context) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queues.clear(ctx.guild.id)
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("You're not in a voice channel.")
                return
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                log.error(f"Voice connect failed: {e}")
                await ctx.send("Could not join your voice channel.")
                return

        vc = ctx.voice_client

        try:
            _, title = extract_stream_url(query)
        except Exception as e:
            await ctx.send(f"Could not find anything for that: {e}")
            return

        self.queues.add(ctx.guild.id, query, title)

        if vc.is_playing() or vc.is_paused():
            await ctx.send(f"Added to queue: {title}")
        else:
            await self.play_next(ctx)

    async def play_next(self, ctx: commands.Context) -> None:
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return

        track = self.queues.pop_next(ctx.guild.id)
        if track is None:
            return

        try:
            stream_url, title = extract_stream_url(track.url)
        except Exception as e:
            log.warning(f"Extraction failed for '{track.title}': {e}")
            await ctx.send(f"Could not load {track.title}, skipping.")
            await self.play_next(ctx)
            return

        def after_playing(error):
            if error:
                log.error(f"Playback error on '{title}': {error}")
            asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

        try:
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
                volume=self.get_volume(ctx.guild.id) / 100,
            )
            vc.play(source, after=after_playing)
        except Exception as e:
            log.error(f"FFmpeg failed to start for '{title}': {e}")
            await ctx.send(f"Playback failed for {title}, skipping.")
            await self.play_next(ctx)
            return

        await ctx.send(f"Now playing: {title}")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command()
    async def pause(self, ctx: commands.Context) -> None:
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command()
    async def resume(self, ctx: commands.Context) -> None:
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    @commands.command()
    async def volume(self, ctx: commands.Context, level: int = None) -> None:
        if level is None:
            await ctx.send(f"Current volume: {self.get_volume(ctx.guild.id)}%")
            return

        if level < 0 or level > 200:
            await ctx.send("Volume must be between 0 and 200.")
            return

        self.volumes[ctx.guild.id] = level

        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = level / 100

        await ctx.send(f"Volume set to {level}%.")

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context) -> None:
        queue = self.queues.get(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty.")
            return

        lines = [f"{i}. {track.title}" for i, track in enumerate(queue, 1)]
        await ctx.send("**Up next:**\n" + "\n".join(lines))

    @commands.command()
    async def remove(self, ctx: commands.Context, index: int) -> None:
        queue = self.queues.get(ctx.guild.id)

        if not queue:
            await ctx.send("The queue is empty.")
            return

        track = self.queues.remove(ctx.guild.id, index)
        if track is None:
            await ctx.send(f"Invalid index. Use a number between 1 and {len(queue)} (see `!queue`).")
            return

        await ctx.send(f"Removed: {track.title}")

    @commands.command()
    async def clear(self, ctx: commands.Context) -> None:
        if not self.queues.get(ctx.guild.id):
            await ctx.send("The queue is already empty.")
            return

        self.queues.clear(ctx.guild.id)
        await ctx.send("Cleared the queue. The current track keeps playing.")

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        self.queues.clear(ctx.guild.id)
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Stopped playback and cleared the queue.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))