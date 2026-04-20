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
from bot.ui import RosterSelector, UndoSelector
import random

last4z = []
last4t = []


# Singular function to get random zones
def get_zone_option(cap):
    loop = True
    ran = 0
    while loop:
        ran = random.randint(1, cap)
        if ran not in last4z:
            loop = False
    if len(last4z) < 4:
        last4z.append(ran)
    else:
        last4z.pop(0)
        last4z.append(ran)
    return ran - 1


def get_event_option():
    options = ["SSH", "WBC", "PDC", "OL"]
    ran = random.randint(1, len(options))
    return options[ran - 1]


class EventManager(commands.Cog, name="EventsManager"):
    """For Direct Management Of Event Systems"""

    def __init__(self, bot: BOKBot):
        self.bot = bot

    @app_commands.command(
        name="trial", description="For Raid Leads: Opens Trial Creation Modal"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def create_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_modal(
            TrialModal(interaction=interaction, bot=self.bot, lang=user_language)
        )

    @app_commands.command(
        name="event", description="For Raid Leads: Opens Event Creation Modal"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def create_event_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_modal(
            EventModal(
                interaction=interaction,
                bot=self.bot,
                lang=user_language,
                channel_id=None,
            )
        )

    @app_commands.command(
        name="modify", description="For Raid Leads: Modify your Trial Roster Details"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def modify_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            f"{self.bot.language[user_language]['replies']['SelectRoster']['Select']}",
            view=RosterSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                cmd_called="modify",
                user_language=user_language,
            ),
        )

    @app_commands.command(
        name="close", description="For Raid Leads: Close out a Roster"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def close_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            f"{self.bot.language[user_language]['replies']['SelectRoster']['Select']}",
            view=RosterSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                cmd_called="close",
                user_language=user_language,
            ),
        )

    @app_commands.command(
        name="prog", description="For Raid Leads: Sets Prog role information"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def set_prog_roles(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_modal(
            ProgModal(self.bot, interaction, user_language)
        )

    @app_commands.command(
        name="runcount",
        description="For Raid Leads: Increases a rosters members run counts.",
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def increase_run_count(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            f"{self.bot.language[user_language]['replies']['SelectRoster']['Select']}",
            view=RosterSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                cmd_called="run_count",
                user_language=user_language,
            ),
        )

    @app_commands.command(
        name="remove", description="For Raid Leads: Remove people from a roster"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def remove_people_from_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            "Select the roster",
            view=RosterSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                cmd_called="remove",
                user_language=user_language,
            ),
        )

    @app_commands.command(
        name="fill", description="For Raid Leads: Fill a roster from backup"
    )
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def fill_roster(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            f"{self.bot.language[user_language]['replies']['SelectRoster']['Select']}",
            view=RosterSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                cmd_called="fill",
                user_language=user_language,
            ),
        )

    @app_commands.command(name="undo", description="For Arma: Undo closing a roster")
    @permissions.application_has_raid_lead()
    @permissions.private_channel_only()
    async def undo_close(self, interaction: Interaction) -> None:
        user_language = Utilities.get_language(interaction.user)
        await interaction.response.send_message(
            f"{self.bot.language[user_language]['replies']['SelectRoster']['Select']}",
            view=UndoSelector(
                interaction=interaction,
                bot=self.bot,
                caller=interaction.user,
                user_language=user_language,
            ),
        )

    @commands.command(name="limits")
    @permissions.has_raid_lead()
    async def print_limits(self, ctx: commands.Context):
        """For Raid Leads: Lists Values of Limits for Rosters"""
        user_language = Utilities.get_language(ctx.author)
        try:
            all_limits = f"{self.bot.language[user_language]['replies']['Limits']}\n"

            for i in range(len(self.bot.limits)):
                if len(self.bot.limits[i]) == 3:
                    all_limits += f"{i}: {self.bot.limits[i][0]} | {self.bot.limits[i][1]} | {self.bot.limits[i][2]}\n"
                else:
                    all_limits += f"{i}: {self.bot.limits[i]}\n"
            await ctx.send(all_limits)
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Incomplete'])}"
            )
            logging.error(f"Print Limits Error: {str(e)}")

    @commands.command(name="pin", aliases=["unpin"])
    @permissions.has_raid_lead()
    async def pin_message(self, ctx: commands.Context):
        """For Raid Leads: Allows pinning of a message"""
        user_language = Utilities.get_language(ctx.author)
        try:
            ref = ctx.message.reference
            if ref is not None:
                # Is a reply - pin or unpin the reply message
                message = await ctx.fetch_message(ref.message_id)
                if message.pinned:
                    await message.unpin()
                    await ctx.reply(
                        f"{self.bot.language[user_language]['replies']['Pin']['Unpinned']}"
                    )
                    return
                else:
                    await message.pin()
                    return
            else:
                # Is not a reply - pin the command message
                await ctx.message.pin()
                return
        except Exception as e:
            await ctx.reply(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"Pin Error: {str(e)}")

    @app_commands.command(
        name="add", description="For Raid Leads: Manually add to roster"
    )
    @app_commands.describe(role="Tank, Healer, or DPS Role to add user into.")
    @app_commands.describe(member="Discord user to add to roster.")
    @permissions.application_has_raid_lead()
    async def add_to_roster(self, interaction: Interaction, role: str, member: Member):
        user_language = Utilities.get_language(interaction.user)
        try:
            user_id = f"{member.id}"
            channel_id = interaction.channel_id
            if not self.bot.rosters.get(channel_id):
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['WrongChannel'])}"
                )
                return
            if member.bot:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NoBots'])}"
                )
                return

            if isinstance(self.bot.rosters[channel_id], EventRoster):
                self.bot.rosters[channel_id].add_member(user_id=user_id, msg="")
                await interaction.response.send_message(
                    f"{member.display_name}: {self.bot.language[user_language]['replies']['EventRoster']['Added']}"
                )

            elif isinstance(self.bot.rosters[channel_id], Roster):
                # Validate the role input
                acceptable_roles = [
                    "dps",
                    "tank",
                    "healer",
                ]  # TODO: Update with multi-lingual later.
                role = role.lower()

                if role not in acceptable_roles:
                    await interaction.response.send_message(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Roster']['AddBad'])}"
                    )
                    return

                logging.info(
                    f"Add called by {interaction.user.display_name} to add {member.display_name} as {role}"
                )

                validation = self.bot.rosters[channel_id].add_member(
                    user_id=user_id, role=role, msg="", which="su"
                )
                if validation == 0:
                    await interaction.response.send_message(
                        f"{member.display_name}: {self.bot.language[user_language]['replies']['Roster']['Added'] % role}"
                    )  # Added into roster
                elif validation == 1:
                    await interaction.response.send_message(
                        f"{member.display_name}: {self.bot.language[user_language]['replies']['Roster']['Full'] % role}"
                    )  # Slots full, added as backup
                    return
                else:  # Unreachable
                    await interaction.response.send_message(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
                    )
                    return

            self.bot.librarian.put_roster(channel_id, self.bot.rosters[channel_id])

        except Exception as e:
            logging.error(f"Add To Roster Error: {str(e)}")
            await interaction.response.send_message(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )

    @app_commands.command(
        name="grant-role", description="For Leads: Gives mentioned user a prog role."
    )
    @app_commands.describe(member="Discord user to grant role to.")
    @app_commands.describe(role="Discord role to grant to the user.")
    @permissions.application_has_prog_lead()
    async def grant_discord_role(
        self, interaction: Interaction, member: Member, role: Role
    ):
        user_language = Utilities.get_language(interaction.user)
        try:
            if member.bot:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NoBots'])}"
                )
                return
            elif interaction.user not in role.members:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NoRole'])}"
                )
                return
            if role.name not in self.bot.limits:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NotProg'])}"
                )
                return
            logging.info(
                f"Grant Role called by {interaction.user.display_name} to grant {role.name} to {member.display_name}"
            )
            await member.add_roles(role)
            await interaction.response.send_message(
                f"{self.bot.language[user_language]['replies']['ProgLeadRole']['Granted'] % (role.name, member.display_name)}"
            )
        except Exception as e:
            logging.error(f"Grant Role Error: {str(e)}")
            raise e

    @app_commands.command(
        name="remove-role", description="For Leads: Removes mentioned user a prog role."
    )
    @app_commands.describe(member="Discord user to remove role from.")
    @app_commands.describe(role="Discord role to remove from user.")
    @permissions.application_has_prog_lead()
    async def remove_discord_role(
        self, interaction: Interaction, member: Member, role: Role
    ):
        user_language = Utilities.get_language(interaction.user)
        try:
            if member.bot:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NoBots'])}"
                )
                return
            elif interaction.user not in role.members:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NoRole'])}"
                )
                return
            if role.name not in self.bot.limits:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['ProgLeadRole']['NotProg'])}"
                )
                return
            logging.info(
                f"Remove Role called by {interaction.user.display_name} to remove {role.name} from {member.display_name}"
            )
            await member.remove_roles(role)
            await interaction.response.send_message(
                f"{self.bot.language[user_language]['replies']['ProgLeadRole']['Removed'] % (role.name, member.display_name)}"
            )
        except Exception as e:
            logging.error(f"Remove Role Error: {str(e)}")
            raise e

    @commands.command(name="event")
    async def random_event(self, ctx: commands.Context):
        """Gives you a random event and zone to do"""
        user_language = Utilities.get_language(ctx.author)
        try:
            options = self.bot.language[user_language]["replies"]["Zones"]
            ran = get_zone_option(len(options))
            event = get_event_option()
            await ctx.send(
                f"{self.bot.language[user_language]['replies']['Events'][event]} {options[ran]}"
            )
        except Exception as e:
            await ctx.reply(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"Get Event Error: {str(e)}")

    @commands.command(name="zone")
    async def random_zone(self, ctx: commands.Context):
        """Gives you a random zone to do for your event"""
        """Gives you a random normal trial to do"""
        user_language = Utilities.get_language(ctx.author)
        try:
            options = self.bot.language[user_language]["replies"]["Zones"]
            ran = get_zone_option(len(options))
            await ctx.send(f"{options[ran]}")
        except Exception as e:
            await ctx.reply(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"Get Zone Error: {str(e)}")

    # Get a trial randomly chosen
    @commands.command(name="ntrial", aliases=["vtrial", "hmtrial"])
    async def generate_trial_to_run(self, ctx: commands.Context):
        """Gives you a random trial to do"""
        user_language = Utilities.get_language(ctx.author)
        try:
            options = self.bot.language[user_language]["replies"]["Trials"]
            loop = True
            ran = 0
            while loop:
                ran = random.randint(1, len(options))
                if ran not in last4t:
                    loop = False
            if len(last4t) < 4:
                last4t.append(ran)
            else:
                last4t.pop(0)
                last4t.append(ran)
            ran = ran - 1
            if ctx.invoked_with == "ntrial":
                await ctx.send(
                    f"{self.bot.language[user_language]['replies']['Events']['Norm']} {options[ran]}"
                )
            elif ctx.invoked_with == "vtrial":
                await ctx.send(
                    f"{self.bot.language[user_language]['replies']['Events']['Vet']} {options[ran]}"
                )
            elif ctx.invoked_with == "hmtrial":
                await ctx.send(
                    f"{self.bot.language[user_language]['replies']['Events']['Vet']} {options[ran]} {self.bot.language[user_language]['replies']['Events']['HM']}"
                )
        except Exception as e:
            await ctx.reply(f"{self.bot.language[user_language]['replies']['Unknown']}")
            logging.error(f"Generate Random Trial Error: {str(e)}")

    # @app_commands.command(name='rank', description='For Officers: Ranks users')
    # @app_commands.describe(role='Healer, Tanks, or DPS')
    # @app_commands.describe(tier='Number based on which tier they qualify for')
    # @app_commands.describe(member='The Member')
    # @permissions.has_officer()
    # async def add_new_rank(self, interaction: Interaction, role: str, member: Member):
    #    user_language = Utilities.get_language(interaction.user)
    #    try:
    #        pass
    #        # TODO: Fetch the correct rank through the config and apply it to the person. Remove higher ranks if needed.
    #        #   If they have the ping tag, apply the appropriate pings.
    #    except Exception as e:
    #        await interaction.response.send_message(
    #            f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}")
    #        logging.error(f"Add To Roster Error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(EventManager(bot))
