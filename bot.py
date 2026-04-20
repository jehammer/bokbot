#!/usr/bin/python3
import asyncio
import logging
import os
import re
import yaml
import shutil
from datetime import datetime
from discord import Intents

from bot.models import BOKBot


def load_configurations():
    full_config = {}
    directory = os.path.join(os.getcwd(), "config")
    if not os.path.exists(directory):
        logging.error(f"The directory {directory} does not exist.")
        return {}
    for filename in os.listdir(directory):
        if (
            filename.endswith(".yaml") or filename.endswith(".yml")
        ) and not filename.lower().startswith("template"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as file:
                file_content = yaml.safe_load(file)
                if isinstance(file_content, dict):
                    full_config.update(file_content)
                else:
                    logging.warning(
                        f"Load Configuration Warning: {filename} is improperly formatted"
                    )
    return full_config


def load_languages():
    languages = {}
    for root, _, files in os.walk("languages"):
        for file in files:
            if file.endswith(".yaml"):
                filepath = os.path.join(root, file)
                language = os.path.basename(root)
                section = os.path.splitext(file)[0]
                if language not in languages:
                    languages[language] = {}
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    languages[language][section] = data
    return languages


def startup_logging():
    log_name = "log.log"
    os.makedirs("logs", exist_ok=True)

    if os.path.exists(log_name):
        now = datetime.now()
        date_str = now.strftime("%m-%d-%Y")

        crash_path = os.path.join("logs", f"log-{date_str}-crash.log")
        v = 1
        while os.path.exists(crash_path):
            crash_path = os.path.join("logs", f"log-{date_str}-crash({v}).log")
            v += 1
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        shutil.move(log_name, crash_path)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: %(message)s",
        handlers=[
            logging.FileHandler(log_name, mode="w"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    now = datetime.now()
    logging.info(
        f"Bot started at: {now.strftime('%I:%M:%S %p')} on {now.strftime('%m-%d-%Y')}\n"
    )


async def main():
    startup_logging()
    config = load_configurations()
    languages = load_languages()
    rosters = {}

    intents = Intents.all()
    intents.members = True

    main_bot = BOKBot(
        config=config,
        rosters=rosters,
        language=languages,
        command_prefix="!",
        case_insensitive=True,
        intents=intents,
    )
    main_bot.remove_command("help")

    for filename in os.listdir("bot/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await main_bot.load_extension(f"bot.cogs.{filename[:-3]}")
                logging.info(f"Successfully loaded {filename}")
            except Exception as e:
                logging.error(f"Failed to load {filename}: {str(e)}")

    async with main_bot:
        await main_bot.start(main_bot.config["bot"]["token"])


if __name__ == "__main__":
    asyncio.run(main())
