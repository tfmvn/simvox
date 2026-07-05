"""
cogs/stats.py
Per-guild listening statistics pulled from the play_history table.
"""
import discord
from discord import app_commands
from discord.ext import commands

from db import repository as repo
from utils.embeds import stats_embed


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Show this server's music listening stats")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stats = await repo.get_guild_stats(interaction.guild_id)
        await interaction.followup.send(embed=stats_embed(interaction.guild.name, stats))


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))