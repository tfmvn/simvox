import discord
from discord.ext import commands
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('TOKEN')

class SimvoxBot(commands.Bot):
    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):

        await self.load_extension("cogs.music")
        

        await self.tree.sync()
        print("✅ Slash commands synced!")

    async def on_ready(self):
        print(f'🔥 Logged in as {self.user.name} (ID: {self.user.id})')
        print('Ready to cook.')


bot = SimvoxBot()

if __name__ == '__main__':
    if TOKEN is None:
        print("❌ Error: DISCORD_TOKEN not found. Check your .env file.")
    else:
        bot.run(TOKEN)