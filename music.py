import discord
from discord.ext import commands
import asyncio
import yt_dlp

from utils.helpers import extract_stream_url

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}
        self.volumes = {}

    def get_queue(self, guild_id: int) -> list:
        return self.queues.setdefault(guild_id, [])

    def get_volume(self, guild_id: int) -> int:
        return self.volumes.setdefault(guild_id, 100)

    @commands.command()
    async def join(self, ctx: commands.Context):
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
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("You're not in a voice channel.")
                return
            await ctx.author.voice.channel.connect()

        vc = ctx.voice_client

        try:
            _, title = extract_stream_url(query)
        except Exception as e:
            await ctx.send(f"Could not find anything for that: {e}")
            return

        queue = self.get_queue(ctx.guild.id)
        queue.append({"url": query, "title": title})

        if vc.is_playing() or vc.is_paused():
            await ctx.send(f"Added to queue: {title}")
        else:
            await self.play_next(ctx)

    async def play_next(self, ctx: commands.Context):
        vc = ctx.voice_client
        queue = self.get_queue(ctx.guild.id)

        if not vc or not queue:
            return

        track = queue.pop(0)

        try:
            stream_url, title = extract_stream_url(track["url"])
        except Exception as e:
            await ctx.send(f"Could not load {track['title']}: {e}")
            await self.play_next(ctx)
            return

        def after_playing(error):
            asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            volume=self.get_volume(ctx.guild.id) / 100,
        )
        vc.play(source, after=after_playing)

        await ctx.send(f"Now playing: {title}")

    @commands.command()
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command()
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command()
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    @commands.command()
    async def volume(self, ctx: commands.Context, level: int = None):
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
    async def show_queue(self, ctx: commands.Context):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty.")
            return

        lines = [f"{i}. {track['title']}" for i, track in enumerate(queue, 1)]
        await ctx.send("**Up next:**\n" + "\n".join(lines))

    @commands.command()
    async def remove(self, ctx: commands.Context, index: int):
        queue = self.get_queue(ctx.guild.id)

        if not queue:
            await ctx.send("The queue is empty.")
            return

        if index < 1 or index > len(queue):
            await ctx.send(f"Invalid index. Use a number between 1 and {len(queue)} (see `!queue`).")
            return

        track = queue.pop(index - 1)
        await ctx.send(f"Removed: {track['title']}")

    @commands.command()
    async def clear(self, ctx: commands.Context):
        queue = self.get_queue(ctx.guild.id)

        if not queue:
            await ctx.send("The queue is already empty.")
            return

        queue.clear()
        await ctx.send("Cleared the queue. The current track keeps playing.")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        self.get_queue(ctx.guild.id).clear()
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Stopped playback and cleared the queue.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))