from discord import CategoryChannel, ForumChannel
from bot.errors import ChannelNotFoundError, GuildNotFoundError, WrongChannelTypeError
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class Validators:
    @staticmethod
    def validate_guild(guild, command_name):
        if guild is None:
            logging.error(f"{command_name}: Guild not found")
            raise GuildNotFoundError(f"{command_name}: Guild not found")

    @staticmethod
    def validate_channel(channel, command_name):
        if channel is None:
            logging.error(f"{command_name}: Channel not found")
            raise ChannelNotFoundError(f"{command_name}: Channel not found")
        elif isinstance(channel, (ForumChannel, CategoryChannel)):
            logging.error(f"{command_name}:  Channel is a Forum or Category Channel")
            raise WrongChannelTypeError(
                f"{command_name}: Channel is a Forum or Category Channel"
            )
