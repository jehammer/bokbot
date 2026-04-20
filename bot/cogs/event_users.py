#!/usr/bin/python3
from discord.ext import commands
from discord import app_commands, Interaction, utils, Member, Role
import logging
import time

# My created imports
from bot import decor as permissions
from bot.errors import *
from bot.modals import *
from bot.models import Roster, Count, EventRoster, BOKBot
from bot.services import Utilities, RosterExtended, EmbedFactory
from bot.ui import RosterSelector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


# TODO: Change zone and trial to use the multi-language support by printing each after second language is added.


# TODO:
#   Create a command to rank someone, if they have the notification tag enabled give them the tier notification tag that they got (T1, T2, T3)
#   And also create a temp mute command that will mute someone in VC for 30 seconds to 5 minutes based on input. Any number 10 and over is seconds otherwise minutes.


class Events(commands.Cog, name="Events"):
    """Commands related to Rosters for Trials, PVP, and other events"""

    def __init__(self, bot: BOKBot):
        self.bot = bot

    @commands.command(name="su", aliases=["signup", "bu", "backup"])
    async def add_user_to_roster(self, ctx: commands.Context):
        """Signs you up to a roster | `!su [optional role] [optional message]`"""
        user_language = Utilities.get_language(ctx.author)
        primary = ["su", "signup", "SU", "SIGNUP"]
        backup = ["bu", "backup", "BU", "BACKUP"]
        user_id = f"{ctx.author.id}"

        try:

            channel_id = ctx.message.channel.id
            try:
                if not self.bot.rosters.get(channel_id):
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['WrongChannel'])}"
                    )
                    return
            except Exception as e:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['DBConError'])}"
                )
                logging.error(f"SU Load Raid Error: {str(e)}")
                return

            if isinstance(self.bot.rosters[channel_id], EventRoster):
                if ctx.invoked_with.lower() in backup:
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['EventRoster']['NoBackup'])}"
                    )
                    return
                # check for a message
                msg = ""
                cmd_vals = ctx.message.content.split(" ", 1)
                if len(cmd_vals) > 1:
                    msg = cmd_vals[1]
                self.bot.rosters[channel_id].add_member(user_id=user_id, msg=msg)
                self.bot.librarian.put_roster(channel_id, self.bot.rosters[channel_id])

                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['EventRoster']['Added']}"
                )
                return

            # Disqualifier check
            if any(
                self.bot.config["raids"]["punish"] in role.name
                for role in ctx.author.roles
            ):
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Punish'])}"
                )
                return

            index = int(self.bot.rosters[channel_id].role_limit)
            prog_role = False
            if index >= 4:
                prog_role = True

            # Check for an override otherwise fetch default.

            acceptable_roles = [
                "dps",
                "tank",
                "healer",
                "heals",
                "heal",
            ]  # TODO: Update this with multi-lingual later.
            healer_roles = ["healer", "heals", "heal"]

            msg = ""
            role = None

            cmd_vals = ctx.message.content.split(" ", 2)
            if len(cmd_vals) > 1 and cmd_vals[1].lower() in acceptable_roles:
                role = cmd_vals[1].lower()
                if len(cmd_vals) > 2:
                    msg = cmd_vals[2]
            elif len(cmd_vals) >= 2:
                if len(cmd_vals) == 2:
                    msg = cmd_vals[1]
                else:
                    msg = cmd_vals[1] + " " + cmd_vals[2]

            if role is None:
                # Check for a default! If there is no default and no role specified then tell the person.
                role = self.bot.librarian.get_default(user_id)
                if role is None:
                    # Role is still none, tell the user there is a problem.
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['NoDefault'] % ctx.invoked_with)}"
                    )
                    return

            if role in healer_roles:
                role = "healer"

            allowed = RosterExtended.validate_join_roster(
                roster_req=index,
                limits=self.bot.limits,
                user=ctx.author,
                roster_role=role,
            )

            if allowed is False and prog_role is False:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['NoRankError'] % (role, self.bot.config['ranks_channel'], index))}"
                )
                return
            elif allowed is False and prog_role is True:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['ProgRoster'])}"
                )
                return

            # TODO: Update with multi-lingual support later.
            which = None
            if ctx.invoked_with.lower() in primary:
                which = "su"
            elif ctx.invoked_with.lower() in backup:
                which = "bu"
            else:
                raise UnknownError(
                    f"Unreachable segment not sure how I got here. SU/BU used was not a valid option!"
                )

            if len(msg) > 50:
                msg = msg[:50]

            validation = self.bot.rosters[channel_id].add_member(
                user_id=user_id, role=role, msg=msg, which=which
            )
            if validation == 0:
                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['Roster']['Added'] % role}"
                )  # Added into roster
            elif validation == 1 and ctx.invoked_with in primary:
                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['Roster']['Full'] % role}"
                )  # Slots full, added as overflow
            elif validation == 1 and ctx.invoked_with in backup:
                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['Roster']['Backup'] % role}"
                )  # Specifically chose Backup
            elif validation == 2:  # Unable to find role
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['NoDefault'] % ctx.invoked_with)}"
                )
                return
            else:  # Unreachable
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
                )
                return

            await ctx.author.add_roles(
                ctx.guild.get_role(self.bot.rosters[channel_id].pingable)
            )
            self.bot.librarian.put_roster(channel_id, self.bot.rosters[channel_id])
        except (UnknownError, NoDefaultError, NoRoleError) as e:
            raise e
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"SUBU Error: {str(e)}")
            return

    @commands.command(name="msg", aliases=["message"])
    async def update_user_message(self, ctx: commands.Context):
        """Update a users message"""
        user_language = Utilities.get_language(ctx.author)
        try:
            channel_id = ctx.message.channel.id
            if not self.bot.rosters.get(channel_id):
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['WrongChannel'])}"
                )
                return

            msg = ""
            msg_vals = ctx.message.content.split(" ", 2)
            if len(msg_vals) == 2:
                msg = msg_vals[1]
            elif len(msg_vals) > 2:
                msg = f"{msg_vals[1]} {msg_vals[2]}"

            if len(msg) > 50:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['MsgLength'])}"
                )
                return

            user_id = f"{ctx.author.id}"
            check = self.bot.rosters[channel_id].update_message(
                user_id=user_id, new_message=msg
            )
            if check:
                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['Roster']['MsgUpdated']}"
                )
            else:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['NotInRoster'])}"
                )
                return
            self.bot.librarian.put_roster(channel_id, self.bot.rosters[channel_id])

        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"MSG Error: {str(e)}")
            return

    @commands.command(name="wd", aliases=["withdraw"])
    async def remove_user_from_roster(self, ctx: commands.Context):
        """Removes you from a roster."""
        user_language = Utilities.get_language(ctx.author)
        try:
            channel_id = ctx.message.channel.id
            try:
                if not self.bot.rosters.get(channel_id):
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['WrongChannel'])}"
                    )
                    return
            except Exception as e:
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['DBConError'])}"
                )
                logging.error(f"WD Load Raid Error: {str(e)}")
                return

            validation = self.bot.rosters[channel_id].remove_member(
                user_id=f"{ctx.author.id}"
            )
            if validation:  # Found and removed from roster
                await ctx.author.remove_roles(
                    ctx.guild.get_role(self.bot.rosters[channel_id].pingable)
                )
                await ctx.reply(
                    f"{self.bot.language[user_language]['replies']['Roster']['Removed']}"
                )
            elif not validation:  # User not in roster
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['NotInRoster'])}"
                )
                return
            else:  # Unreachable
                await ctx.reply(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
                )
                return

            self.bot.librarian.put_roster(
                channel_id=channel_id, data=self.bot.rosters[channel_id]
            )

        except (UnknownError, NoDefaultError, NoRoleError) as e:
            raise e
        except Exception as e:
            await ctx.send(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"WD Error: {str(e)}")
            return

    @commands.command(name="status")
    async def send_status_embed(self, ctx: commands.Context):
        """Posts the current roster information"""
        user_language = Utilities.get_language(ctx.author)
        guild = ctx.message.author.guild
        ui_lang = self.bot.language[user_language]["ui"]
        try:
            channel_id = ctx.message.channel.id

            if self.bot.rosters.get(channel_id) is None:
                await ctx.send(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['WrongChannel'])}"
                )
                return

            if isinstance(self.bot.rosters[channel_id], EventRoster):
                embed = EmbedFactory.create_event_roster(
                    roster=self.bot.rosters[channel_id],
                    bot=self.bot,
                    language=ui_lang["EventStatus"],
                    guild=guild,
                )
                await ctx.send(embed=embed)
                return

            if isinstance(
                self.bot.limits[self.bot.rosters[channel_id].role_limit], list
            ):
                # Need to work with 3 roles to check, dps | tank | healer order
                limiter_dps = utils.get(
                    guild.roles,
                    name=self.bot.limits[self.bot.rosters[channel_id].role_limit][0],
                )
                limiter_tank = utils.get(
                    guild.roles,
                    name=self.bot.limits[self.bot.rosters[channel_id].role_limit][1],
                )
                limiter_healer = utils.get(
                    guild.roles,
                    name=self.bot.limits[self.bot.rosters[channel_id].role_limit][2],
                )

                roles_req = f"{limiter_dps.mention} {limiter_tank.mention} {limiter_healer.mention}"
            else:
                limiter = utils.get(
                    guild.roles,
                    name=self.bot.limits[self.bot.rosters[channel_id].role_limit],
                )
                roles_req = f"{limiter.mention}"

            embed = EmbedFactory.create_status(
                roster=self.bot.rosters[channel_id],
                bot=self.bot,
                language=ui_lang["Status"],
                roles_req=roles_req,
                guild=guild,
            )

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.reply(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"Status Error: {str(e)}")
            return

    @commands.command(name="default")
    @permissions.language()
    async def set_default_role(self, ctx: commands.Context, role="check", **kwargs):
        """Set or check your default for rosters | `!default [optional: role]`"""
        # TODO: Make Role mapper for this from the supported languages to dps, healer, or tank
        # TODO: Make it so this can be deleted with entering Clear or None as possible options
        # TODO: Make this set peoples color role based on the default when this is set if posible.
        language = kwargs.get("language")
        try:
            role = role.lower()
            user_id = ctx.message.author.id
            if role.lower() == "heal" or role.lower() == "heals":
                role = "healer"
            if role == "dps" or role == "healer" or role == "tank":
                try:
                    self.bot.librarian.put_default(user_id=user_id, default=role)
                    await ctx.reply(
                        f"{ctx.message.author.display_name}: {self.bot.language[language]['replies']['Default']['Set'] % role}"
                    )
                except Exception as e:
                    await ctx.reply(
                        f"{Utilities.format_error(language, self.bot.language[language]['replies']['DBConError'])}"
                    )
                    logging.error(f"Default error: {str(e)}")
                    return
            elif role == "check":
                try:
                    default = self.bot.librarian.get_default(user_id)
                    if default is None:
                        await ctx.reply(
                            f"{ctx.message.author.display_name}: {self.bot.language[language]['replies']['Default']['NoneSet']}"
                        )
                    else:
                        await ctx.reply(
                            f"{ctx.message.author.display_name} {self.bot.language[language]['replies']['Default']['Answer']} {default}"
                        )
                except Exception as e:
                    await ctx.send(
                        f"{Utilities.format_error(language, self.bot.language[language]['replies']['DBConError'])}"
                    )
                    logging.error(f"Default error: {str(e)}")
                    return
            else:
                await ctx.reply(
                    f"{Utilities.format_error(language, self.bot.language[language]['replies']['Default']['BadRoleError'])}"
                )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(language, self.bot.language[language]['replies']['DBConError'])}"
            )
            logging.error(f"Default Role Set Error: {str(e)}")

    @commands.command(name="count")
    async def check_own_count(self, ctx: commands.Context):
        """A way for people to check their number of raid runs"""
        user_language = Utilities.get_language(ctx.author)
        try:
            counts: Count = self.bot.librarian.get_count(ctx.author.id)
            if counts is not None:
                embed = EmbedFactory.create_count(
                    counts,
                    self.bot.language[user_language]["ui"]["Count"],
                    ctx.author.display_name,
                    ctx.guild.name,
                )
                await ctx.reply(embed=embed)
            else:
                await ctx.send(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Count']['NoHistory'])}"
                )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['DBConError'])}"
            )
            logging.error(f"Count check error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(Events(bot))
