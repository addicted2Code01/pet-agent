import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from src.core.agent import PetAgent

load_dotenv()

class PetSitterBot(commands.Bot):
    def __init__(self, agent: PetAgent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Check if it's a command (starts with /)
        if message.content.startswith('/'):
            await self.handle_command(message)
        else:
            # It's a regular chat message - pass to the agent
            async with message.channel.typing():
                response = await self.agent.chat(str(message.author), message.content)
                await message.reply(response)

        # Process other commands
        await self.process_commands(message)

    async def handle_command(self, message: discord.Message):
        """Handles custom commands like /fed, /meds, etc."""
        parts = message.content.split()
        command = parts[0].lower()

        if command == "/fed":
            # Usage: /fed Luna
            if len(parts) < 2:
                await message.reply("Please specify the pet. Usage: `/fed Luna`")
                return
            
            pet_name = parts[1]
            pet = self.agent.get_pet_by_name(pet_name)
            if not pet:
                await message.reply(f"I couldn't find a pet named `{pet_name}`.")
                return

            await message.reply(f"Logging feeding for {pet.name}...")
            result = self.agent.log_activity(pet.id, "Feeding", "completed")
            await message.reply(result)

        elif command == "/meds":
            # Usage: /meds Luna
            if len(parts) < 2:
                await message.reply("Please specify the pet. Usage: `/meds Luna`")
                return
            
            pet_name = parts[1]
            pet = self.agent.get_pet_by_name(pet_name)
            if not pet:
                await message.reply(f"I couldn't find a pet named `{pet_name}`.")
                return

            await message.reply(f"Logging medication for {pet.name}...")
            result = self.agent.log_activity(pet.id, "Medication", "completed")
            await message.reply(result)
        
        elif command == "/status":
            # Usage: /status Luna
            if len(parts) < 2:
                await message.reply("Please specify the pet. Usage: `/status Luna`")
                return
            
            pet_name = parts[1]
            pet = self.agent.get_pet_by_name(pet_name)
            if not pet:
                await message.reply(f"I couldn't find a pet named `{pet_name}`.")
                return

            info = self.agent.get_pet_info(pet.id)
            await message.reply(info)

        else:
            await message.reply(f"Unknown command: `{command}`. Try `/fed`, `/meds`, or `/status`.")

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        return

    agent = PetAgent()
    intents = discord.Intents.default()
    intents.message_content = True # Required to read message content

    bot = PetSitterBot(agent, command_prefix='/', intents=intents)
    
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
