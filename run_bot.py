# The Discord bot is disabled for now: Discord routes every message through
# Discord's servers, which conflicts with the local-only privacy goal. The
# dashboard's Sitter View chat replaces it. Code is kept in
# src/interfaces/discord_bot.py for a possible later phase.
import sys

if __name__ == "__main__":
    sys.exit("The Discord bot is disabled. Use the dashboard instead: python3 run_dashboard.py")
