"""
utils/helpers.py
Small utility functions shared across the codebase.
"""
import discord
from typing import Optional


async def send_error(interaction: discord.Interaction, message: str, ephemeral: bool = True):
    from utils.embeds import error_embed
    e = error_embed(message)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=e, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=e, ephemeral=ephemeral)
    except Exception:
        pass


async def send_success(interaction: discord.Interaction, message: str, ephemeral: bool = False):
    from utils.embeds import success_embed
    e = success_embed(message)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=e, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=e, ephemeral=ephemeral)
    except Exception:
        pass


def fmt_time(seconds: int) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def parse_time(time_str: str) -> Optional[int]:
    """Parse mm:ss or ss into total seconds. Returns None on failure."""
    try:
        parts = time_str.strip().split(":")
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None

