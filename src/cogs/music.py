import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from core.scraper import search_audio
from core.player import GuildMusicManager

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.managers = {}

    def get_manager(self, guild_id: int) -> GuildMusicManager:
        if guild_id not in self.managers:
            self.managers[guild_id] = GuildMusicManager(self.bot, guild_id)
        return self.managers[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return None

        channel = interaction.user.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if not voice_client:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        manager = self.get_manager(interaction.guild_id)
        manager.voice_client = voice_client
        return manager

    @app_commands.command(name="play", description="Play or queue a track instantly")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()
        
        manager = await self.ensure_voice(interaction)
        if not manager:
            return

        try:

            track = await asyncio.to_thread(search_audio, query)
            
            manager.add_to_queue(track)

            if not manager.voice_client.is_playing() and not manager.voice_client.is_paused():
                await manager.play_next()
                await interaction.followup.send(f"🎶 Now playing: **{track['title']}**")
            else:
                await interaction.followup.send(f"⏳ Added to queue: **{track['title']}** (Position: {len(manager.queue)})")
        except Exception as e:
            await interaction.followup.send(f"❌ Playback/Scraping error: {e}")

    @app_commands.command(name="pause", description="Pause the currently playing track")
    async def pause(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.pause():
            await interaction.response.send_message("⏸️ Playback paused.")
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the paused track")
    async def resume(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.resume():
            await interaction.response.send_message("▶️ Playback resumed.")
        else:
            await interaction.response.send_message("❌ Playback isn't paused.", ephemeral=True)

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        if manager.voice_client and (manager.voice_client.is_playing() or manager.voice_client.is_paused()):
            manager.skip()
            await interaction.response.send_message("⏭️ Skipped current track.")
        else:
            await interaction.response.send_message("❌ Nothing to skip.", ephemeral=True)

    @app_commands.command(name="queue", description="Show the upcoming tracks")
    async def queue(self, interaction: discord.Interaction):
        manager = self.get_manager(interaction.guild_id)
        
        embed = discord.Embed(title="📋 Current Queue", color=discord.Color.blurple())
        
        if manager.current:
            embed.add_field(name="Now Playing", value=manager.current['title'], inline=False)
        else:
            embed.description = "Queue is empty! Use `/play` to add a track."
            await interaction.response.send_message(embed=embed)
            return

        if manager.queue:
            queue_list = ""
            for idx, track in enumerate(manager.queue, start=1):
                queue_list += f"`{idx}.` {track['title']}\n"
                if idx >= 10:
                    queue_list += f"...and {len(manager.queue) - 10} more tracks."
                    break
            embed.add_field(name="Up Next", value=queue_list, inline=False)
        else:
            embed.add_field(name="Up Next", value="No songs queued up.", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))