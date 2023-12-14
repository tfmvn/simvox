import discord
from discord.ext import commands
import yt_dlp

from utils.helpers import extract_stream_url

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
    async def play(self, ctx: commands.Context, url: str):
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("You're not in a voice channel.")
                return
            await ctx.author.voice.channel.connect()

        vc = ctx.voice_client

        if vc.is_playing():
            vc.stop()

        try:
            stream_url, title = extract_stream_url(url)
        except Exception as e:
            await ctx.send(f"Could not load that URL: {e}")
            return

        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        vc.play(source)

        await ctx.send(f"Now playing: {title}")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Stopped playback.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
