import discord
from discord import app_commands
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="ping", description="Test if Simvox is awake")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong! The kitchen is open.")


async def setup(bot):
    await bot.add_cog(Music(bot))