import os
import sys
import asyncio

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.interfaces.discord_bot import main

if __name__ == "__main__":
    asyncio.run(main())
