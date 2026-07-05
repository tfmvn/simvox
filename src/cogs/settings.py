"""
cogs/settings.py
Server configuration commands: DJ role, 24/7 mode, audio quality,
SponsorBlock toggle, idle timeout.
All require "Manage Server" permission to change (read-only /settings view
is open to everyone).
"""
import discord
from discord import app_commands
from discord.ext import commands

from db import repository as repo
from utils.embeds import settings_embed, success_embed, error_embed, quality_embed


def _manage_guild():
    def predicate(interaction: discord.Interaction) -> bool:
        return isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)


settings_group = app_commands.Group(name="settings", description="Configure Simvox for this server")


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @settings_group.command(name="view", description="Show current server settings")
    async def view_settings(self, interaction: discord.Interaction):
        settings = await repo.get_guild_settings(interaction.guild_id)
        dj_role = interaction.guild.get_role(settings["dj_role_id"]) if settings["dj_role_id"] else None
        await interaction.response.send_message(embed=settings_embed(settings, dj_role))

    @settings_group.command(name="djrole", description="Set the DJ role (only DJs can control playback)")
    @app_commands.describe(role="Role to designate as DJ — omit to clear it")
    @_manage_guild()
    async def djrole(self, interaction: discord.Interaction, role: discord.Role = None):
        await repo.set_dj_role(interaction.guild_id, role.id if role else None)
        if role:
            await interaction.response.send_message(embed=success_embed(f"DJ role set to {role.mention}."))
        else:
            await interaction.response.send_message(embed=success_embed("DJ role cleared — anyone can control playback."))

    @settings_group.command(name="sponsorblock", description="Toggle automatic sponsor segment skipping")
    @app_commands.describe(enabled="Turn SponsorBlock on or off")
    @_manage_guild()
    async def sponsorblock(self, interaction: discord.Interaction, enabled: bool):
        await repo.set_sponsorblock(interaction.guild_id, enabled)
        state = "enabled 🟢" if enabled else "disabled 🔴"
        await interaction.response.send_message(embed=success_embed(f"SponsorBlock {state}."))

    @settings_group.command(name="idletimeout", description="Minutes of inactivity before auto-disconnect")
    @app_commands.describe(minutes="1-60 minutes")
    @_manage_guild()
    async def idletimeout(self, interaction: discord.Interaction, minutes: app_commands.Range[int, 1, 60]):
        await repo.set_idle_timeout(interaction.guild_id, minutes * 60)
        await interaction.response.send_message(embed=success_embed(f"Idle timeout set to {minutes} minutes."))

    @djrole.error
    @sponsorblock.error
    @idletimeout.error
    async def settings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=error_embed("You need **Manage Server** permission to change settings."),
                ephemeral=True,
            )

    # ── /247 ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="247", description="Toggle 24/7 mode — bot stays in voice even when idle")
    @app_commands.describe(enabled="Turn 24/7 mode on or off")
    @_manage_guild()
    async def twentyfourseven(self, interaction: discord.Interaction, enabled: bool):
        await repo.set_247(interaction.guild_id, enabled)
        state = "enabled 🟢 — I'll stay connected" if enabled else "disabled 🔴 — I'll leave when idle"
        await interaction.response.send_message(embed=success_embed(f"24/7 mode {state}."))

    @twentyfourseven.error
    async def tfs_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=error_embed("You need **Manage Server** permission to change this."),
                ephemeral=True,
            )

    # ── /quality ─────────────────────────────────────────────────────────────

    @app_commands.command(name="quality", description="Set audio quality (affects bandwidth/CPU usage)")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low (lightest)", value="low"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="High (recommended)", value="high"),
        app_commands.Choice(name="Source (uncapped)", value="source"),
    ])
    @_manage_guild()
    async def quality(self, interaction: discord.Interaction, level: app_commands.Choice[str]):
        await repo.set_quality(interaction.guild_id, level.value)
        music_cog = self.bot.get_cog("Music")
        if music_cog:
            manager = music_cog.get_manager(interaction.guild_id)
            manager.set_quality(level.value)
        await interaction.response.send_message(embed=quality_embed(level.value))

    @quality.error
    async def quality_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=error_embed("You need **Manage Server** permission to change quality."),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    cog = Settings(bot)
    bot.tree.add_command(settings_group)
    await bot.add_cog(cog)