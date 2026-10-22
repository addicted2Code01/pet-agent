import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
from src.core.agent import PetAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def split_message(text: str, limit: int = 1900) -> list[str]:
    """Splits a string into chunks smaller than the limit."""
    return [text[i:i+limit] for i in range(0, len(text), limit)]

class PetSitterBot(commands.Bot):
    def __init__(self, agent: PetAgent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent
        self.allowed_user_ids = []
        self.allowed_channel_ids = []
        
        # Load allowlist from .env
        user_ids_str = os.getenv("ALLOWED_USER_IDS", "")
        if user_ids_str:
            self.allowed_user_ids = [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip().isdigit()]
            
        channel_ids_str = os.getenv("ALLOWED_CHANNEL_IDS", "")
        if channel_ids_str:
            self.allowed_channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(",") if cid.strip().isdigit()]

    async def setup_hook(self):
        """Called when the bot is starting up. Used to sync slash commands."""
        # Sync slash commands to Discord
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

    async def on_message(self, message: discord.Message):
        # Item 2: Ignore bots and unauthorized users
        if message.author.bot:
            return

        if self.allowed_user_ids and message.author.id not in self.allowed_user_ids:
            return
            
        if self.allowed_channel_ids and message.channel.id not in self.allowed_channel_ids:
            return

        # If it's a slash command, it's handled by the tree, so we don't do anything here.
        # However, the user wants a conversational agent for regular messages.
        if not message.content.startswith('/'):
            async with message.channel.typing():
                response = await self.agent.chat(str(message.author.id), message.content)
                # Item 19: Handle long replies
                for chunk in split_message(response):
                    await message.reply(chunk)

        await self.process_commands(message)

class PetSitterCommandTree(app_commands.CommandTree):
    """Custom tree to handle commands with the agent."""
    def __init__(self, bot: PetSitterBot):
        super().__init__(bot)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Item 2: Security check for slash commands
        if self.bot.allowed_user_ids and interaction.user.id not in self.bot.allowed_user_ids:
            await interaction.response.send_message("You are not authorized to use this bot.", ephemeral=True)
            return False
        if self.bot.allowed_channel_ids and interaction.channel_id not in self.bot.allowed_channel_ids:
            await interaction.response.send_message("This command is not allowed in this channel.", ephemeral=True)
            return False
        return True

# We'll use a slightly different approach to attach slash commands
# to the bot instance since we need the agent.

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables.")
        return

    agent = PetAgent()
    intents = discord.Intents.default()
    intents.message_content = True 

    bot = PetSitterBot(agent, command_prefix='/', intents=intents)
    
    # Define slash commands
    @bot.tree.command(name="fed", description="Log feeding for a pet")
    @app_commands.describe(pet_name="The name of the pet (e.g., Luna)")
    async def fed(interaction: discord.Interaction, pet_name: str):
        pet = agent.get_pet_by_name(pet_name)
        if not pet:
            await interaction.response.send_message(f"I couldn't find a pet named `{pet_name}`.", ephemeral=True)
            return
        
        await interaction.response.defer()
        result = agent.log_activity(pet.id, "Feeding", "completed")
        # Item 19: Split message
        for chunk in split_message(result):
            await interaction.followup.send(chunk)

    @bot.tree.command(name="meds", description="Log medication for a pet")
    @app_commands.describe(pet_name="The name of the pet (e.g., Luna)")
    async def meds(interaction: discord.Interaction, pet_name: str):
        pet = agent.get_pet_by_name(pet_name)
        if not pet:
            await interaction.response.send_message(f"I couldn't find a pet named `{pet_name}`.", ephemeral=True)
            return
        
        await interaction.response.defer()
        result = agent.log_activity(pet.id, "Medication", "completed")
        for chunk in split_message(result):
            await interaction.followup.send(chunk)

    @bot.tree.command(name="status", description="Get info about a pet")
    @app_commands.describe(pet_name="The name of the pet (e.g., Luna)")
    async def status(interaction: discord.Interaction, pet_name: str):
        pet = agent.get_pet_by_name(pet_name)
        if not pet:
            await interaction.response.send_message(f"I couldn't find a pet named `{pet_name}`.", ephemeral=True)
            return
        
        info = agent.get_pet_info(pet.id)
        for chunk in split_message(info):
            await interaction.response.send_message(chunk)

    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
