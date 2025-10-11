"""Main entry point for the bot."""
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot import MetinBot


def main():
    """Main entry point for stone farming."""
    bot = MetinBot.create_stone_farming_bot("config.json")

    try:
        bot.run()
    except Exception as e:
        bot.logger.error("Something went wrong! Auto exiting in 10s!")
        bot.logger.error(str(e))
        time.sleep(10)
        raise


def main_mining():
    """Entry point for ore mining."""
    bot = MetinBot.create_ore_mining_bot("config.json")

    try:
        bot.run()
    except Exception as e:
        bot.logger.error("Something went wrong! Auto exiting in 10s!")
        bot.logger.error(str(e))
        time.sleep(10)
        raise


def main_dungeon():
    """Entry point for dungeon running."""
    bot = MetinBot.create_dungeon_bot("config.json")

    try:
        bot.run()
    except Exception as e:
        bot.logger.error("Something went wrong! Auto exiting in 10s!")
        bot.logger.error(str(e))
        time.sleep(10)
        raise


if __name__ == "__main__":
    main()
