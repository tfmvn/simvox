"""
cogs/music.py
All core playback slash commands for Simvox.
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging

from core.player      import GuildMusicManager
from core.resolver     import resolve, detect_source, SourceType
from core.idle         import IdleTracker
from core.permissions  import require_dj
from db                import repository as repo
from ui.views import (
    SearchView, NowPlayingView, QueueView,
    FilterView, LoopView, VoteSkipView, LyricsView,
)
from utils.embeds import (
    now_playing, queue_embed, search_results, error_embed,
    success_embed, info_embed, history_embed, filters_embed,
    volume_embed, quality_embed, track_added, _fmt_time,
)
from utils.helpers import parse_time

log = logging.getLogger("simvox.music")


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot          = bot
        self.managers: dict[int, GuildMusicManager] = {}
        self.idle_tracker = IdleTracker(bot)

    # ── Internal helpers ────────────────────────────────────────────────────

    def get_manager(self, guild_id: int) -> GuildMusicManager:
        if guild_id not in self.managers:
            manager = GuildMusicManager(self.bot, guild_id)
            manager.idle_tracker = self.idle_tracker
            self.managers[guild_id] = manager
        return self.managers[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction) -> GuildMusicManager | None:
        if not interaction.user.voice:
            await _send_error(interaction, "You need to be in a voice channel first.")
            return None

        channel = interaction.user.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        manager = self.get_manager(interaction.guild_id)
        manager.voice_client = vc

        settings = await repo.get_guild_settings(interaction.guild_id)
        manager.set_quality(settings["quality"])

        self.idle_tracker.notify_activity(interaction.guild_id)
        return manager

    async def _queue_autocomplete(self, interaction: discord.Interaction, current: str):
        """Shared autocomplete for /remove and /move position args — shows track titles."""
        manager = self.get_manager(interaction.guild_id)
        choices = []
        for i, t in enumerate(manager.queue[:25], start=1):
            label = f"{i}. {t['title'][:80]}"
            choices.append(app_commands.Choice(name=label, value=i))
        if current:
            try:
                num = int(current)
                choices = [c for c in choices if str(num) in str(c.value)] or choices
            except ValueError:
                choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]

    # ── Lifecycle hooks ──────────────────────────────────────────────────────

    async def restore_all_guilds(self):
        """Called once on bot startup — reconnects to guilds with saved state."""
        guild_ids = await repo.all_saved_guild_ids()
        for guild_id in guild_ids:
            try:
                state = await repo.load_queue_state(guild_id)
                if not state:
                    continue
                manager = self.get_manager(guild_id)
                await manager.restore_state(state)

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                if state["voice_channel_id"]:
                    channel = guild.get_channel(state["voice_channel_id"])
                    if channel:
                        vc = await channel.connect()
                        manager.voice_client = vc
                        if state["text_channel_id"]:
                            manager.text_channel = guild.get_channel(state["text_channel_id"])
                        await manager.play_next()
                        log.info(f"Restored playback for guild {guild_id}")
            except Exception as e:
                log.warning(f"Failed to restore guild {guild_id}: {e}")

    # ── /play ────────────────────────────────────────────────────────────────

    @app_commands.command(name="play", description="Search and play a track (YouTube, SoundCloud, or search)")
    @app_commands.describe(query="Song name, artist, YouTube URL, or SoundCloud URL")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send(embed=error_embed("Join a voice channel first!"))
            return

        try:
            tracks = await resolve(query)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return

        # A URL resolving to multiple tracks = playlist/album → queue all.
        # Plain text search returning multiple tracks → show picker menu.
        is_url = detect_source(query) != SourceType.SEARCH

        if len(tracks) == 1 or is_url:
            manager = await self.ensure_voice(interaction)
            if not manager:
                return

            for t in tracks:
                t["requested_by"] = interaction.user.id
                t["requested_by_name"] = interaction.user.display_name
                manager.add_to_queue(t)
            manager.text_channel = interaction.channel

            first = tracks[0]
            if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
                await manager.play_next()
                embed = now_playing(first, 0, interaction.user, manager=manager)
                view  = NowPlayingView(manager)
                msg   = await interaction.followup.send(embed=embed, view=view)
                manager.np_message = msg
            else:
                if len(tracks) == 1:
                    pos = len(manager.queue)
                    eta = manager.eta_for_queue_index(pos - 1)
                    await interaction.followup.send(embed=track_added(first, pos, eta_seconds=eta))
                else:
                    await interaction.followup.send(
                        embed=success_embed(f"Queued **{len(tracks)}** tracks.")
                    )
        else:
            embed = search_results(query, tracks)
            view  = SearchView(tracks, self)
            await interaction.followup.send(embed=embed, view=view)

    # ── /nowplaying ──────────────────────────────────────────────────────────

    @app_commands.command(name="nowplaying", description="Show what's currently playing")
    async def nowplaying(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if not manager.current:
            await interaction.response.send_message(embed=info_embed("Nothing Playing", "Queue is empty."))
            return
        embed = now_playing(manager.current, manager.position, manager=manager)
        view  = NowPlayingView(manager)
        await interaction.response.send_message(embed=embed, view=view)
        manager.np_message   = await interaction.original_response()
        manager.text_channel = interaction.channel

    # ── /pause ───────────────────────────────────────────────────────────────

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.pause():
            await interaction.response.send_message(embed=success_embed("Playback paused."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing is playing."), ephemeral=True)

    # ── /resume ──────────────────────────────────────────────────────────────

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.resume():
            await interaction.response.send_message(embed=success_embed("Playback resumed."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing is paused."), ephemeral=True)

    # ── /skip ────────────────────────────────────────────────────────────────

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        if manager.skip():
            await interaction.response.send_message(embed=success_embed("Skipped."))
        else:
            await interaction.response.send_message(embed=error_embed("Nothing to skip."), ephemeral=True)

    # ── /voteskip ────────────────────────────────────────────────────────────

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

    # ── /queue ───────────────────────────────────────────────────────────────

    @app_commands.command(name="queue", description="Show the current queue with ETAs")
    async def queue(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        embed   = queue_embed(manager, 0)
        view    = QueueView(manager, 0)
        await interaction.response.send_message(embed=embed, view=view)

    # ── /remove ──────────────────────────────────────────────────────────────

    @app_commands.command(name="remove", description="Remove a track from the queue")
    @app_commands.describe(position="Track to remove")
    async def remove(self, interaction: discord.Interaction, position: int):
        if not await require_dj(interaction):
            return
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

    @remove.autocomplete("position")
    async def remove_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._queue_autocomplete(interaction, current)

    # ── /move ────────────────────────────────────────────────────────────────

    @app_commands.command(name="move", description="Move a track to a different queue position")
    @app_commands.describe(from_pos="Track to move", to_pos="Target position")
    async def move(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        if manager.move(from_pos, to_pos):
            await interaction.response.send_message(
                embed=success_embed(f"Moved track from `#{from_pos}` to `#{to_pos}`.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed("Invalid position(s)."), ephemeral=True
            )

    @move.autocomplete("from_pos")
    async def move_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self._queue_autocomplete(interaction, current)

    # ── /shuffle ─────────────────────────────────────────────────────────────

    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        if not manager.queue:
            await interaction.response.send_message(embed=error_embed("Queue is empty."), ephemeral=True)
            return
        manager.shuffle()
        await interaction.response.send_message(embed=success_embed(f"🔀 Shuffled {len(manager.queue)} tracks."))

    # ── /clear ───────────────────────────────────────────────────────────────

    @app_commands.command(name="clear", description="Clear the entire queue")
    async def clear(self, interaction: discord.Interaction):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        count   = len(manager.queue)
        manager.clear_queue()
        await interaction.response.send_message(embed=success_embed(f"Cleared {count} tracks from the queue."))

    # ── /loop ────────────────────────────────────────────────────────────────

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

    # ── /volume ──────────────────────────────────────────────────────────────

    @app_commands.command(name="volume", description="Set playback volume (0–200)")
    @app_commands.describe(level="Volume level 0–200 (default 100)")
    async def volume(self, interaction: discord.Interaction, level: app_commands.Range[int, 0, 200]):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        manager.set_volume(level)
        await interaction.response.send_message(embed=volume_embed(level))

    # ── /seek ────────────────────────────────────────────────────────────────

    @app_commands.command(name="seek", description="Seek to a position in the current track")
    @app_commands.describe(timestamp="Time to seek to, e.g. 1:30 or 90")
    async def seek(self, interaction: discord.Interaction, timestamp: str):
        if not await require_dj(interaction):
            return
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

    # ── /replay ──────────────────────────────────────────────────────────────

    @app_commands.command(name="replay", description="Replay the current track from the beginning")
    async def replay(self, interaction: discord.Interaction):
        await interaction.response.defer()
        manager = self.get_manager(interaction.guild_id)
        if await manager.replay():
            await interaction.followup.send(embed=success_embed("⏮ Replaying from start."))
        else:
            await interaction.followup.send(embed=error_embed("Nothing is playing."))

    # ── /filter ──────────────────────────────────────────────────────────────

    @app_commands.command(name="filter", description="Apply an audio filter")
    async def filter(self, interaction: discord.Interaction):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        embed   = filters_embed(manager.active_filter)
        view    = FilterView(manager)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ── /autoplay ────────────────────────────────────────────────────────────

    @app_commands.command(name="autoplay", description="Toggle smart autoplay of recommended tracks")
    async def autoplay(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        manager.autoplay = not manager.autoplay
        state = "enabled 🟢" if manager.autoplay else "disabled 🔴"
        await interaction.response.send_message(embed=success_embed(f"Autoplay {state}."))

    # ── /history ─────────────────────────────────────────────────────────────

    @app_commands.command(name="history", description="Show recently played tracks")
    async def history(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        await interaction.response.send_message(embed=history_embed(manager.history))

    # ── /disconnect ──────────────────────────────────────────────────────────

    @app_commands.command(name="disconnect", description="Disconnect the bot from voice")
    async def disconnect(self, interaction: discord.Interaction):
        if not await require_dj(interaction):
            return
        manager = self.get_manager(interaction.guild_id)
        self.idle_tracker.notify_activity(interaction.guild_id)
        await manager.disconnect()
        await interaction.response.send_message(embed=success_embed("Disconnected. See ya. 👋"))

    # ── /playtop ─────────────────────────────────────────────────────────────

    @app_commands.command(name="playtop", description="Add a track to the top of the queue")
    @app_commands.describe(query="Song name, artist, or URL")
    async def playtop(self, interaction: discord.Interaction, query: str):
        if not await require_dj(interaction):
            return
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send(embed=error_embed("Join a voice channel first!"))
            return

        try:
            tracks = await resolve(query)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return

        manager = await self.ensure_voice(interaction)
        if not manager:
            return

        track = tracks[0]
        track["requested_by"] = interaction.user.id
        track["requested_by_name"] = interaction.user.display_name
        manager.queue.insert(0, track)
        manager.text_channel = interaction.channel

        if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
            await manager.play_next()
            embed = now_playing(track, 0, interaction.user, manager=manager)
            view  = NowPlayingView(manager)
            msg   = await interaction.followup.send(embed=embed, view=view)
            manager.np_message = msg
        else:
            await interaction.followup.send(embed=track_added(track, 1, eta_seconds=manager.eta_for_queue_index(0)))

    # ── /search ──────────────────────────────────────────────────────────────

    @app_commands.command(name="search", description="Search for tracks without playing immediately")
    @app_commands.describe(query="What to search for")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            tracks = await resolve(query)
            if len(tracks) == 1:
                from core.scraper import search_top_tracks
                tracks = await asyncio.to_thread(search_top_tracks, query, 10)
        except Exception as e:
            await interaction.followup.send(embed=error_embed(str(e)))
            return
        embed = search_results(query, tracks)
        view  = SearchView(tracks, self)
        await interaction.followup.send(embed=embed, view=view)

    # ── /lyrics ──────────────────────────────────────────────────────────────

    @app_commands.command(name="lyrics", description="Get real lyrics for the current or a specified track")
    @app_commands.describe(query="Override song name (optional)")
    async def lyrics(self, interaction: discord.Interaction, query: str = ""):
        await interaction.response.defer()
        manager = self.get_manager(interaction.guild_id)
        title   = query or (manager.current["title"] if manager.current else "")
        if not title:
            await interaction.followup.send(embed=error_embed("Nothing is playing and no query provided."))
            return

        from core.lyrics import fetch_lyrics, paginate_lyrics
        from utils.embeds import lyrics_embed

        result = await fetch_lyrics(title)
        if not result:
            await interaction.followup.send(embed=error_embed(
                f"No lyrics found for **{title[:80]}**. Try `/lyrics query:Artist - Song Title` for a more precise match."
            ))
            return

        resolved_title, lyrics_text = result
        pages = paginate_lyrics(lyrics_text)
        embed = lyrics_embed(resolved_title, pages[0], 0, len(pages))
        if len(pages) > 1:
            view = LyricsView(resolved_title, pages)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed)

    # ── /help ────────────────────────────────────────────────────────────────

    @app_commands.command(name="help", description="Show all Simvox commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎵  SIMVOX — Command Reference", color=0xE8132A)
        sections = {
            "🎶 Playback": [
                ("`/play [query]`",      "Search and pick from top 10 results"),
                ("`/playtop [query]`",   "Jump to front of queue"),
                ("`/search [query]`",    "Browse without auto-playing"),
                ("`/nowplaying`",        "Live now-playing card with controls"),
                ("`/pause` / `/resume`", "Pause / resume"),
                ("`/skip`",              "Force skip (DJ only)"),
                ("`/voteskip`",          "Democratic skip"),
                ("`/replay`",            "Restart current track"),
                ("`/seek [mm:ss]`",      "Jump to timestamp"),
            ],
            "📋 Queue": [
                ("`/queue`",             "Paginated queue viewer with ETAs"),
                ("`/remove [pos]`",      "Remove by position (autocomplete)"),
                ("`/move [from] [to]`",  "Reorder tracks (autocomplete)"),
                ("`/shuffle`",           "Randomise queue (DJ only)"),
                ("`/clear`",             "Wipe queue (DJ only)"),
                ("`/history`",           "Last 15 played"),
            ],
            "🎵 Playlists": [
                ("`/playlist create`",   "Make a new playlist"),
                ("`/playlist save`",     "Save current queue into one"),
                ("`/playlist load`",     "Queue up a saved playlist"),
                ("`/playlist list`",     "Your saved playlists"),
                ("`/playlist delete`",   "Delete a playlist"),
            ],
            "⚙️ Settings": [
                ("`/volume [0–200]`",    "Set volume (DJ only)"),
                ("`/loop`",              "Off / Track / Queue"),
                ("`/filter`",            "Bass boost, Nightcore, 8D, Vaporwave… (DJ only)"),
                ("`/autoplay`",          "Toggle smart recommended-track autoplay"),
                ("`/lyrics`",            "Real lyrics, paginated"),
                ("`/quality`",           "Audio bitrate tier (Manage Server)"),
                ("`/247`",               "Stay in voice 24/7 (Manage Server)"),
                ("`/settings view`",     "See DJ role, 24/7, SponsorBlock, etc."),
                ("`/settings djrole`",   "Restrict controls to a role"),
                ("`/settings sponsorblock`", "Toggle sponsor-segment auto-skip"),
                ("`/settings idletimeout`",  "Auto-disconnect delay"),
                ("`/stats`",             "Server listening stats"),
                ("`/disconnect`",        "Leave voice (DJ only)"),
            ],
        }
        for section, cmds in sections.items():
            value = "\n".join(f"{cmd} — {desc}" for cmd, desc in cmds)
            embed.add_field(name=section, value=value, inline=False)
        embed.set_footer(text="SIMVOX  •  Red by design.")
        await interaction.response.send_message(embed=embed)


async def _send_error(interaction: discord.Interaction, message: str):
    from utils.embeds import error_embed
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=error_embed(message))
        else:
            await interaction.response.send_message(embed=error_embed(message), ephemeral=True)
    except Exception:
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))