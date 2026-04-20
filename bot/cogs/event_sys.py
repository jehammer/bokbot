import random

from discord import Game, app_commands, Interaction
from discord.ext import commands
import logging
import time

# My created imports
from bot import decor as permissions
from bot.errors.boterrors import (
    NoDefaultError,
    NoRoleError,
    NotPrivateError,
    UnknownError,
)
from bot.models import BOKBot
from bot.services import RosterExtended


class BotSystems(commands.Cog, name="BotSystems"):
    """Listeners for BOKBot events and dispatches and creator-only commands for maintenance"""

    def __init__(self, bot: BOKBot):
        self.bot = bot

    async def on_tree_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You're missing permissions to use that"
            )
        elif isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(f"{str(error)}")
        elif isinstance(error, NotPrivateError):
            await interaction.response.send_message(f"{str(error)}", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Some weird error is being thrown. Not sure what it is"
            )
            logging.error(f"{str(error)}")

    @commands.Cog.listener()
    async def on_ready(self):

        if self.bot.user is None:
            return

        logging.info(f"Logged in as: {self.bot.user.name}")

        # Set Presence
        await self.bot.change_presence(
            activity=Game(name=self.bot.config["presence_message"])
        )

        fetched = self.bot.librarian.get_all_rosters()
        if fetched is not None:
            self.bot.rosters = fetched
            logging.info("Found and Loaded Rosters")
        else:
            logging.info("No Rosters Found")
        fetched = RosterExtended.get_limits(
            librarian=self.bot.librarian, roles_config=self.bot.config["raids"]["ranks"]
        )
        if fetched is not None:
            self.bot.limits = fetched
            logging.info("Found and Loaded Limits")
        else:
            logging.info("No Limits Found")

        self.bot.tree.on_error = self.on_tree_error

        logging.info("Bot is ready for use")

    @commands.Cog.listener()
    async def on_sort_rosters(self):
        try:
            # Order Channels correctly now
            new_positions = RosterExtended.sort_rosters(self.bot.rosters)
            for i in new_positions:
                channel = self.bot.get_channel(i)
                await channel.edit(position=new_positions[i])
                time.sleep(2)
        except Exception as e:
            logging.error(f"Position Change Error: {str(e)}")
            return

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            styles = ["(ツ)", "(•_•)", "(°_°)", "(¬‿¬)", "(ಠ_ಠ)"]
            shrug = f"¯\\\\\\_{random.choice(styles)}\\_/¯"
            await ctx.reply(f"{shrug}")
        elif isinstance(error, commands.MissingRole):
            await ctx.reply(
                f"You do not have permission to use this command. {str(error)}"
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.reply("You are not my creator. You may not use this command.")
        elif isinstance(error, UnknownError):
            logging.error(f"UNKNOWN ERROR REACHED: {str(error)}")
            await ctx.reply(
                "Unreachable code has been reached. Logging details. I bet you are Lily or Arma..."
            )
        elif isinstance(error, NoDefaultError):
            await ctx.reply(f"{str(error)}")
        elif isinstance(error, NoRoleError):
            await ctx.reply(f"{str(error)}")
        elif isinstance(error, NotPrivateError):
            await ctx.reply(f"{str(error)}")
        else:
            await ctx.send(
                "Unable to complete the command. I am not sure which error was thrown."
            )
            logging.error(f"Generic Error: {str(error)}")

    # TODO: Add listener for role change to update the color of a person to their default role.

    # Creator-Only commands

    @commands.command(name="roster")
    @permissions.creator_only()
    async def printout_roster(self, ctx: commands.Context, channel_id):
        """Printout a roster directly for any debugging needs"""
        try:
            await ctx.reply(rosters[str(channel_id)].get_roster_data())
        except Exception as e:
            await ctx.reply(f"Unable to complete: {str(e)}")

    @commands.command(name="allrosters")
    @permissions.creator_only()
    async def printout_all_rosters(self, ctx: commands.Context):
        """Printout all rosters directly for any debugging needs"""
        try:
            for i in self.bot.rosters:
                await ctx.reply(self.bot.rosters[i].get_roster_data())
        except Exception as e:
            await ctx.reply(f"Unable to complete: {str(e)}")

    @commands.command(name="saverosters")
    @permissions.creator_only()
    async def save_roster_info(self, ctx: commands.Context):
        """Force Save current Roster Map and Rosters"""
        try:
            for (
                i
            ) in self.bot.rosters:  # TODO: make it save based on roster instance type
                self.bot.librarian.put_roster(i, rosters[i].get_roster_data())
            await ctx.reply("Rosters saved.")

        except Exception as e:
            await ctx.reply(f"Unable to complete: {str(e)}")

    @commands.command(name="reloadrosters")
    @permissions.creator_only()
    async def reload_roster_info(self, ctx: commands.Context):
        """Force Reload all Roster information"""
        try:
            logging.info("Force Reload Roster Information Called")
            global rosters

            fetched = self.bot.librarian.get_all_rosters()
            if fetched is not None:
                rosters = fetched
                logging.info("Found and Loaded Rosters")
            await ctx.reply("Roster Information Reloaded.")
        except Exception as e:
            await ctx.reply("Unable to complete: {str(e)}")

    @commands.command(name="resort")
    @permissions.creator_only()
    async def force_resort_rosters(self, ctx: commands.Context):
        """Force all Rosters to be sorted again."""
        try:
            new_positions = RosterExtended.sort_rosters(rosters)
            for i in new_positions:
                channel = self.bot.get_channel(i)
                await channel.edit(position=new_positions[i])  # type: ignore
                time.sleep(2)
            await ctx.reply("Finished Sorting!")
        except Exception as e:
            await ctx.reply(f"Unable to complete: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(BotSystems(bot))
