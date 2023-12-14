import discord
from discord.ext import commands
import logging

import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("simvox")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.music")


if __name__ == "__main__":
    bot.run(config.TOKEN)
