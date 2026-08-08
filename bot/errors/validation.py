from discord import CategoryChannel, ForumChannel, TextChannel, VoiceChannel, abc
from bot.errors import ChannelNotFoundError, GuildNotFoundError, WrongChannelTypeError
import logging
from typing import Any, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")

SendableChannel = Union[TextChannel, VoiceChannel]


class Validators:
    @staticmethod
    def validate_guild(guild):
        if guild is None:
            raise GuildNotFoundError("Guild not found")

    @staticmethod
    def validate_channel(channel: Any) -> abc.Messageable:
        if channel is None:
            logging.error("Channel not found")
            raise ChannelNotFoundError("Channel not found")

        elif isinstance(channel, (ForumChannel, CategoryChannel)):
            logging.error("Channel is a Forum or Category Channel")
            raise WrongChannelTypeError("Channel is a Forum or Category Channel")
        return channel
