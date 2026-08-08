from discord.ext import commands
from discord import app_commands


import inspect


class AutoDataException(Exception):
    """Base exception that automatically grabs local data from where it was raised."""

    def __init__(self, message="An error occurred"):
        # Index [1] gets the frame of the function that raised THIS exception
        caller_frame = inspect.stack()[1].frame

        # Save variables directly to the instance
        self.function_name = caller_frame.f_code.co_name

        # Format the default message with the data
        detailed_msg = f"{self.function_name}: {message}\n"
        super().__init__(detailed_msg)


class EventGuildNotFoundError(AutoDataException):
    """Raised when a guild is not found in an event listener."""

    pass


class EventChannelNotFoundError(AutoDataException):
    """Raised when a channel is not found in an event listener."""

    pass


class EventChannelInvalidTypeError(AutoDataException):
    """Raised when a channel is of an invalid type in an event listener."""

    pass


class IODBError(Exception):
    pass


class DiscordError(Exception):
    pass


class UserError(Exception):
    pass


class NoDefaultError(commands.CommandError):
    pass


class DefaultIOError(Exception):
    pass


class UnknownError(commands.CommandError):
    pass


class NoRoleError(commands.CommandError):
    pass


class BotUserError(Exception):
    pass


class NotPrivateError(app_commands.AppCommandError):
    pass


class MissingInteractionError(app_commands.AppCommandError):
    pass


class AppCommandGuildNotFoundError(app_commands.AppCommandError):
    pass


class MissingRoleError(app_commands.AppCommandError):
    pass


class CommandGuildNotFoundError(commands.CommandError):
    pass


class AppCommandGuildNotFoundError(app_commands.AppCommandError):
    pass


class PrivateChannelNotFoundError(AutoDataException):
    pass


class ChannelNotFoundError(AutoDataException):
    pass


class WrongChannelTypeError(AutoDataException):
    pass
