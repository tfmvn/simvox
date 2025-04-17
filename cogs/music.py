import discord
from discord.ext import commands
import logging

from core.player import PlayerManager
from utils.helpers import extract_stream_url

log = logging.getLogger("simvox.music")


def _has_audio(voice_client: discord.VoiceClient | None) -> bool:
    """True if a voice client is currently playing or paused."""
    return bool(voice_client) and (voice_client.is_playing() or voice_client.is_paused())


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.player = PlayerManager(bot)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        # The bot itself got disconnected (kicked, moved out, connection drop, etc.)
        if member.id == self.bot.user.id and after.channel is None:
            self.player.reset(member.guild.id)
            log.info(f"Bot left voice in {member.guild.name} — state reset.")
            return

        # Everyone else left the channel the bot is in — leave and clean up.
        vc = member.guild.voice_client
        if vc and vc.channel and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()
            self.player.reset(member.guild.id)
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
            self.player.reset(ctx.guild.id)
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

        self.player.enqueue(ctx.guild.id, query, title)

        if _has_audio(vc):
            await ctx.send(f"Added to queue: {title}")
        else:
            await self.player.play_next(vc, ctx.guild.id, ctx.send)

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        if _has_audio(ctx.voice_client):
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command()
    async def loop(self, ctx: commands.Context) -> None:
        enabled = self.player.toggle_loop(ctx.guild.id)
        state = "enabled 🔁 — the current song will repeat" if enabled else "disabled"
        await ctx.send(f"Looping {state}.")

    @commands.command()
    async def shuffle(self, ctx: commands.Context) -> None:
        queue = self.player.queues.get(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty — nothing to shuffle.")
            return

        self.player.queues.shuffle(ctx.guild.id)
        await ctx.send("Shuffled the queue.")

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
            await ctx.send(f"Current volume: {self.player.get_volume(ctx.guild.id)}%")
            return

        if level < 0 or level > 200:
            await ctx.send("Volume must be between 0 and 200.")
            return

        self.player.set_volume(ctx.guild.id, level, ctx.voice_client)
        await ctx.send(f"Volume set to {level}%.")

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context) -> None:
        queue = self.player.queues.get(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty.")
            return

        lines = [f"{i}. {track.title}" for i, track in enumerate(queue, 1)]
        await ctx.send("**Up next:**\n" + "\n".join(lines))

    @commands.command()
    async def remove(self, ctx: commands.Context, index: int) -> None:
        queue = self.player.queues.get(ctx.guild.id)

        if not queue:
            await ctx.send("The queue is empty.")
            return

        track = self.player.queues.remove(ctx.guild.id, index)
        if track is None:
            await ctx.send(f"Invalid index. Use a number between 1 and {len(queue)} (see `!queue`).")
            return

        await ctx.send(f"Removed: {track.title}")

    @commands.command()
    async def clear(self, ctx: commands.Context) -> None:
        if not self.player.queues.get(ctx.guild.id):
            await ctx.send("The queue is already empty.")
            return

        self.player.queues.clear(ctx.guild.id)
        await ctx.send("Cleared the queue. The current track keeps playing.")

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        self.player.reset(ctx.guild.id)
        if _has_audio(ctx.voice_client):
            ctx.voice_client.stop()
            await ctx.send("Stopped playback and cleared the queue.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
