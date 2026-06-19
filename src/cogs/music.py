"""
cogs/music.py
All slash commands for Simvox.
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging

from core.player  import GuildMusicManager
from core.scraper import search_top_tracks, fetch_by_url
from ui.views     import (
    SearchView, NowPlayingView, QueueView,
    FilterView, LoopView, VoteSkipView,
)
from utils.embeds import (
    now_playing, queue_embed, search_results, error_embed,
    success_embed, info_embed, history_embed, filters_embed,
    volume_embed, _fmt_time,
)
from utils.helpers import send_error, send_success, parse_time

log = logging.getLogger("simvox.music")


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot      = bot
        self.managers: dict[int, GuildMusicManager] = {}


    def get_manager(self, guild_id: int) -> GuildMusicManager:
        if guild_id not in self.managers:
            self.managers[guild_id] = GuildMusicManager(self.bot, guild_id)
        return self.managers[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction) -> GuildMusicManager | None:
        if not interaction.user.voice:
            await send_error(interaction, "You need to be in a voice channel first.")
            return None

        channel = interaction.user.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        manager = self.get_manager(interaction.guild_id)
        manager.voice_client = vc
        return manager


    @app_commands.command(name="play", description="Search and play a track")
    @app_commands.describe(query="Song name, artist, or YouTube URL")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send(embed=error_embed("Join a voice channel first!"))
            return

        try:
            if query.startswith("http"):
                tracks = [await asyncio.to_thread(fetch_by_url, query)]
            else:
                tracks = await asyncio.to_thread(search_top_tracks, query, 10)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return

        if len(tracks) == 1:

            manager = await self.ensure_voice(interaction)
            if not manager:
                return
            manager.add_to_queue(tracks[0])
            manager.text_channel = interaction.channel

            if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
                await manager.play_next()
                embed = now_playing(tracks[0], 0, interaction.user)
                view  = NowPlayingView(manager)
                msg   = await interaction.followup.send(embed=embed, view=view)
                manager.np_message = msg
            else:
                from utils.embeds import track_added
                pos = len(manager.queue)
                await interaction.followup.send(embed=track_added(tracks[0], pos))
        else:
            embed = search_results(query, tracks)
            view  = SearchView(tracks, self)
            await interaction.followup.send(embed=embed, view=view)


    @app_commands.command(name="nowplaying", description="Show what's currently playing")
    async def nowplaying(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if not manager.current:
            await interaction.response.send_message(embed=info_embed("Nothing Playing", "Queue is empty."))
            return
        embed = now_playing(manager.current, manager.position)
        view  = NowPlayingView(manager)
        msg   = await interaction.response.send_message(embed=embed, view=view)
        manager.np_message   = await interaction.original_response()
        manager.text_channel = interaction.channel


    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.pause():
            await interaction.response.send_message(embed=success_embed("Playback paused."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing is playing."), ephemeral=True)


    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.resume():
            await interaction.response.send_message(embed=success_embed("Playback resumed."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing is paused."), ephemeral=True)


    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.skip():
            await interaction.response.send_message(embed=success_embed("Skipped."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing to skip."), ephemeral=True)


    @app_commands.command(name="voteskip", description="Start a vote to skip the current track")
    async def voteskip(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if not manager.current:
            await interaction.response.send_message(embed=error_embed("Nothing is playing."), ephemeral=True)
            return

        vc = manager.voice_client
        if not vc:
            await interaction.response.send_message(embed=error_embed("Bot isn't in a voice channel."), ephemeral=True)
            return

        listeners = [m for m in vc.channel.members if not m.bot]
        required  = max(2, (len(listeners) + 1) // 2)

        embed = discord.Embed(
            title="⏭  Vote Skip",
            description=f"**{manager.current['title']}**\nNeed `{required}` votes to skip.",
            color=0xE8132A,
        )
        view = VoteSkipView(manager, required)
        await interaction.response.send_message(embed=embed, view=view)


    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        embed   = queue_embed(manager, 0)
        view    = QueueView(manager, 0)
        await interaction.response.send_message(embed=embed, view=view)


    @app_commands.command(name="remove", description="Remove a track from the queue by position")
    @app_commands.describe(position="Queue position to remove (1 = next up)")
    async def remove(self, interaction: discord.Interaction, position: int):
        manager = self.get_manager(interaction.guild_id)
        track   = manager.remove(position)
        if track:
            await interaction.response.send_message(
                embed=success_embed(f"Removed **{track['title']}** from position {position}.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(f"No track at position {position}."), ephemeral=True
            )


    @app_commands.command(name="move", description="Move a track to a different queue position")
    @app_commands.describe(from_pos="Current position", to_pos="Target position")
    async def move(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        manager = self.get_manager(interaction.guild_id)
        if manager.move(from_pos, to_pos):
            await interaction.response.send_message(
                embed=success_embed(f"Moved track from `#{from_pos}` to `#{to_pos}`.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("Invalid position(s)."), ephemeral=True
            )


    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if not manager.queue:
            await interaction.response.send_message(embed=error_embed("Queue is empty."), ephemeral=True)
            return
        manager.shuffle()
        await interaction.response.send_message(embed=success_embed(f"🔀 Shuffled {len(manager.queue)} tracks."))


    @app_commands.command(name="clear", description="Clear the entire queue")
    async def clear(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        count   = len(manager.queue)
        manager.clear_queue()
        await interaction.response.send_message(embed=success_embed(f"Cleared {count} tracks from the queue."))


    @app_commands.command(name="loop", description="Set loop mode")
    async def loop(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        view    = LoopView(manager)
        modes   = {"off": "Off", "track": "🔂 Track", "queue": "🔁 Queue"}
        embed   = info_embed(
            "🔁  Loop Mode",
            f"Current: **{modes.get(manager.loop_mode,'Off')}**\n\nPick a new mode below."
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    @app_commands.command(name="volume", description="Set playback volume (0–200)")
    @app_commands.describe(level="Volume level 0–200 (default 100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        if not 0 <= level <= 200:
            await interaction.response.send_message(
                embed=error_embed("Volume must be between 0 and 200."), ephemeral=True
            )
            return
        manager = self.get_manager(interaction.guild_id)
        manager.set_volume(level)
        await interaction.response.send_message(embed=volume_embed(level))


    @app_commands.command(name="seek", description="Seek to a position in the current track")
    @app_commands.describe(timestamp="Time to seek to, e.g. 1:30 or 90")
    async def seek(self, interaction: discord.Interaction, timestamp: str):
        await interaction.response.defer()
        seconds = parse_time(timestamp)
        if seconds is None:
            await interaction.followup.send(embed=error_embed("Invalid timestamp. Use `mm:ss` or seconds."))
            return
        manager = self.get_manager(interaction.guild_id)
        if await manager.seek(seconds):
            await interaction.followup.send(embed=success_embed(f"⏩ Seeked to `{_fmt_time(seconds)}`."))
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing."))


    @app_commands.command(name="replay", description="Replay the current track from the beginning")
    async def replay(self, interaction: discord.Interaction):
        await interaction.response.defer()
        manager = self.get_manager(interaction.guild_id)
        if await manager.replay():
            await interaction.followup.send(embed=success_embed("⏮ Replaying from start."))
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing."))


    @app_commands.command(name="filter", description="Apply an audio filter")
    async def filter(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        embed   = filters_embed(manager.active_filter)
        view    = FilterView(manager)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    @app_commands.command(name="autoplay", description="Toggle autoplay of related tracks")
    async def autoplay(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        manager.autoplay = not manager.autoplay
        state = "enabled 🟢" if manager.autoplay else "disabled 🔴"
        await interaction.response.send_message(embed=success_embed(f"Autoplay {state}."))


    @app_commands.command(name="history", description="Show recently played tracks")
    async def history(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        await interaction.response.send_message(embed=history_embed(manager.history))


    @app_commands.command(name="disconnect", description="Disconnect the bot from voice")
    async def disconnect(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        await manager.disconnect()
        await interaction.response.send_message(embed=success_embed("Disconnected. See ya. 👋"))


    @app_commands.command(name="playtop", description="Add a track to the top of the queue")
    @app_commands.describe(query="Song name, artist, or YouTube URL")
    async def playtop(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send(embed=error_embed("Join a voice channel first!"))
            return

        try:
            if query.startswith("http"):
                tracks = [await asyncio.to_thread(fetch_by_url, query)]
            else:
                tracks = await asyncio.to_thread(search_top_tracks, query, 1)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return

        manager = await self.ensure_voice(interaction)
        if not manager:
            return

        track = tracks[0]
        manager.queue.insert(0, track)
        manager.text_channel = interaction.channel

        if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
            await manager.play_next()
            embed = now_playing(track, 0, interaction.user)
            view  = NowPlayingView(manager)
            msg   = await interaction.followup.send(embed=embed, view=view)
            manager.np_message = msg
        else:
            from utils.embeds import track_added
            await interaction.followup.send(embed=track_added(track, 1))


    @app_commands.command(name="search", description="Search for tracks without playing immediately")
    @app_commands.describe(query="What to search for")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            tracks = await asyncio.to_thread(search_top_tracks, query, 10)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return
        embed = search_results(query, tracks)
        view  = SearchView(tracks, self)
        await interaction.followup.send(embed=embed, view=view)


    @app_commands.command(name="lyrics", description="Search for lyrics of the current or a specified track")
    @app_commands.describe(query="Override song name (optional)")
    async def lyrics(self, interaction: discord.Interaction, query: str = ""):
        await interaction.response.defer()
        manager = self.get_manager(interaction.guild_id)
        title   = query or (manager.current["title"] if manager.current else "")
        if not title:
            await interaction.followup.send(embed=error_embed("Nothing is playing and no query provided."))
            return

        embed = discord.Embed(
            title=f"🎤  Lyrics: {title[:80]}",
            description=(
                "Simvox doesn't bundle a lyrics provider to avoid rate-limit and copyright issues.\n\n"
                f"🔎 **[Search on Genius](https://genius.com/search?q={discord.utils.escape_markdown(title).replace(' ','+')})**\n"
                f"🔎 **[Search on AZLyrics](https://www.azlyrics.com/lyrics/{title.replace(' ','').lower()[:30]}.html)**"
            ),
            color=0xE8132A,
        )
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="help", description="Show all Simvox commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎵  SIMVOX — Command Reference",
            color=0xE8132A,
        )
        sections = {
            "🎶 Playback": [
                ("`/play [query]`",      "Search and pick from top 10 results"),
                ("`/playtop [query]`",   "Jump to front of queue"),
                ("`/search [query]`",    "Browse without auto-playing"),
                ("`/nowplaying`",        "Live now-playing card with controls"),
                ("`/pause`",             "Pause"),
                ("`/resume`",            "Resume"),
                ("`/skip`",              "Force skip"),
                ("`/voteskip`",          "Democratic skip"),
                ("`/replay`",            "Restart current track"),
                ("`/seek [mm:ss]`",      "Jump to timestamp"),
            ],
            "📋 Queue": [
                ("`/queue`",             "Paginated queue viewer"),
                ("`/remove [pos]`",      "Remove by position"),
                ("`/move [from] [to]`",  "Reorder tracks"),
                ("`/shuffle`",           "Randomise queue"),
                ("`/clear`",             "Wipe queue"),
                ("`/history`",           "Last 15 played"),
            ],
            "⚙️ Settings": [
                ("`/volume [0–200]`",    "Set volume level"),
                ("`/loop`",              "Off / Track / Queue"),
                ("`/filter`",            "Bass boost, Nightcore, 8D, Vaporwave…"),
                ("`/autoplay`",          "Toggle autoplay of related tracks"),
                ("`/lyrics`",            "Find lyrics for current track"),
                ("`/disconnect`",        "Disconnect from voice"),
            ],
        }
        for section, cmds in sections.items():
            value = "\n".join(f"{cmd} — {desc}" for cmd, desc in cmds)
            embed.add_field(name=section, value=value, inline=False)
        embed.set_footer(text="SIMVOX  •  Red by design.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))

