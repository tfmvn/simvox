"""
cogs/playlist.py
Personal playlist system, scoped per-guild-per-user. Stored as JSON blobs
in SQLite via db.repository.
"""
import discord
from discord import app_commands
from discord.ext import commands

from db import repository as repo
from utils.embeds import playlist_embed, playlist_list_embed, success_embed, error_embed


class Playlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Group defined as a Cog attribute so self is always bound ────────────
    playlist_group = app_commands.Group(
        name="playlist",
        description="Save and load your own playlists",
    )

    # ── Autocomplete ─────────────────────────────────────────────────────────

    async def _playlist_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = await repo.list_playlists(interaction.guild_id, interaction.user.id)
        return [
            app_commands.Choice(name=n, value=n)
            for n in names
            if current.lower() in n.lower()
        ][:25]

    # ── Commands ─────────────────────────────────────────────────────────────

    @playlist_group.command(name="create", description="Create a new empty playlist")
    @app_commands.describe(name="Name for your new playlist")
    async def create(self, interaction: discord.Interaction, name: str):
        ok = await repo.create_playlist(interaction.guild_id, interaction.user.id, name)
        if ok:
            await interaction.response.send_message(
                embed=success_embed(f"Created playlist **{name}**.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(f"You already have a playlist named **{name}**."),
                ephemeral=True,
            )

    @playlist_group.command(name="save", description="Save the current queue into a playlist")
    @app_commands.describe(name="Playlist to save into (must already exist)")
    @app_commands.autocomplete(name=_playlist_autocomplete)
    async def save(self, interaction: discord.Interaction, name: str):
        music_cog = self.bot.get_cog("Music")
        manager = music_cog.get_manager(interaction.guild_id) if music_cog else None
        if not manager or (not manager.current and not manager.queue):
            await interaction.response.send_message(
                embed=error_embed("Nothing is playing or queued."), ephemeral=True
            )
            return

        tracks = ([manager.current] if manager.current else []) + list(manager.queue)
        ok = await repo.save_playlist_tracks(
            interaction.guild_id, interaction.user.id, name, tracks
        )
        if ok:
            await interaction.response.send_message(
                embed=success_embed(f"Saved {len(tracks)} tracks to **{name}**.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(
                    f"No playlist named **{name}** — use `/playlist create` first."
                ),
                ephemeral=True,
            )

    @playlist_group.command(name="load", description="Load a playlist into the queue")
    @app_commands.describe(name="Playlist to load")
    @app_commands.autocomplete(name=_playlist_autocomplete)
    async def load(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        tracks = await repo.load_playlist(interaction.guild_id, interaction.user.id, name)
        if tracks is None:
            await interaction.followup.send(
                embed=error_embed(f"No playlist named **{name}**.")
            )
            return
        if not tracks:
            await interaction.followup.send(
                embed=error_embed(f"Playlist **{name}** is empty.")
            )
            return

        if not interaction.user.voice:
            await interaction.followup.send(
                embed=error_embed("Join a voice channel first!")
            )
            return

        music_cog = self.bot.get_cog("Music")
        manager = await music_cog.ensure_voice(interaction)
        if not manager:
            return

        for t in tracks:
            manager.add_to_queue(t)
        manager.text_channel = interaction.channel

        if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
            await manager.play_next()

        await interaction.followup.send(
            embed=success_embed(
                f"Loaded **{len(tracks)}** tracks from **{name}** into the queue."
            )
        )

    @playlist_group.command(name="list", description="Show all your saved playlists")
    async def list_cmd(self, interaction: discord.Interaction):
        names = await repo.list_playlists(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message(
            embed=playlist_list_embed(names), ephemeral=True
        )

    @playlist_group.command(name="view", description="Preview the tracks in a playlist")
    @app_commands.describe(name="Playlist to preview")
    @app_commands.autocomplete(name=_playlist_autocomplete)
    async def view_cmd(self, interaction: discord.Interaction, name: str):
        tracks = await repo.load_playlist(interaction.guild_id, interaction.user.id, name)
        if tracks is None:
            await interaction.response.send_message(
                embed=error_embed(f"No playlist named **{name}**."), ephemeral=True
            )
            return
        await interaction.response.send_message(embed=playlist_embed(name, tracks))

    @playlist_group.command(name="delete", description="Delete one of your playlists")
    @app_commands.describe(name="Playlist to delete")
    @app_commands.autocomplete(name=_playlist_autocomplete)
    async def delete(self, interaction: discord.Interaction, name: str):
        ok = await repo.delete_playlist(interaction.guild_id, interaction.user.id, name)
        if ok:
            await interaction.response.send_message(
                embed=success_embed(f"Deleted playlist **{name}**.")
            )
        else:
            await interaction.response.send_message(
                embed=error_embed(f"No playlist named **{name}**."), ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Playlist(bot))
    # The group is registered automatically because it's a Cog class attribute.
    # Do NOT call bot.tree.add_command(playlist_group) here — that would
    # double-register it and cause a CommandAlreadyRegistered error.