"""
core/permissions.py
DJ role gating. A user can perform "DJ-only" actions (skip, clear, shuffle,
volume, filter, etc.) if ANY of the following is true:
  - No DJ role is configured for the guild (open mode)
  - They have the configured DJ role
  - They have the "Manage Server" permission (mods/admins always bypass)
  - They are the only non-bot human in the voice channel
"""
import discord
from db import repository as repo


async def is_dj(interaction: discord.Interaction) -> bool:
    """
    Check whether the user behind this interaction is allowed to do
    DJ-only stuff (skip, clear, shuffle, volume, filters...).

    Returns True if the DM case applies (no guild), the user is a mod
    (Manage Server), the DJ role isn't configured at all, they actually
    have the DJ role, or they're the only human currently in the voice
    channel. Otherwise False.
    """
    if not interaction.guild:
        return True  # DMs have no DJ concept, just let it through

    member = interaction.user
    if isinstance(member, discord.Member) and member.guild_permissions.manage_guild:
        return True

    settings = await repo.get_guild_settings(interaction.guild_id)
    dj_role_id = settings.get("dj_role_id")

    if dj_role_id is None:
        return True  # no DJ role configured — open to everyone

    if isinstance(member, discord.Member):
        if any(r.id == dj_role_id for r in member.roles):
            return True

        # Solo-in-VC exemption — if you're by yourself with the bot there's
        # no one to annoy, so don't make people ask a mod to skip their own song
        if member.voice and member.voice.channel:
            humans = [m for m in member.voice.channel.members if not m.bot]
            if len(humans) <= 1:
                return True

    return False


async def require_dj(interaction: discord.Interaction) -> bool:
    """
    Same check as is_dj(), but also handles the response for you.

    Sends an ephemeral "you need the DJ role" error and returns False if
    the check fails, otherwise just returns True and does nothing else.
    Callers should do `if not await require_dj(interaction): return`.
    """
    if await is_dj(interaction):
        return True

    from utils.embeds import error_embed
    settings = await repo.get_guild_settings(interaction.guild_id)
    role_mention = f"<@&{settings['dj_role_id']}>"
    await interaction.response.send_message(
        embed=error_embed(f"This requires the {role_mention} role (or be alone in voice)."),
        ephemeral=True,
    )
    return False