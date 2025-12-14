"""
main.py
Entry point: loads config, builds the bot, registers cogs, and runs it.
"""
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # reads TOKEN (and anything else) from a local .env file
TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("simvox")

intents = discord.Intents.default()
intents.message_content = True  # needed to read the "!" prefix in messages
intents.voice_states = True     # needed to know who's in which voice channel

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.music")


if __name__ == "__main__":
    if not TOKEN:
        log.critical("TOKEN not set. Copy .env.example to .env and add your bot token.")
    else:
        bot.run(TOKEN)