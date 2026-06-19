import discord
from discord import app_commands
from discord.ext import commands
from core.scraper import search_audio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="Play a song by searching or pasting a URL")
    async def play(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()


        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel first!")
            return

        channel = interaction.user.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)


        if not voice_client:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        try:

            data = search_audio(query)
            

            ffmpeg_options = {
                'options': '-vn',
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            }
            

            audio_source = discord.FFmpegPCMAudio(data['source'], **ffmpeg_options)
            
            if not voice_client.is_playing():
                voice_client.play(audio_source)
                await interaction.followup.send(f"🎶 Now playing: **{data['title']}**")
            else:
                await interaction.followup.send(f"⚠️ I'm already playing something! (Queue system coming later)")

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Music(bot))