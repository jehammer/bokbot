import discord
from discord import Member, Message, User, utils, ForumChannel, CategoryChannel
from discord.ext import commands, tasks
import logging
import asyncio

import datetime
import shutil
import re
import yaml
import os
import time
import calendar

from bot.errors.boterrors import PrivateChannelNotFoundError
from bot.errors.validation import Validators
from bot.models import Roster, EventRoster
from bot.models import BOKBot
from bot.services import Utilities, embed_factory
from bot.errors import GuildNotFoundError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")

scheduled_time = datetime.time(13, 0, 0, 0)

default = None
ranks = None
poons = None
other = None


def gather_roles(guild, config):
    """Loads the starting roles for people when joining"""
    global default
    global ranks
    global poons
    global other
    default = utils.get(guild.roles, name=config["roles"]["default"])
    ranks = utils.get(guild.roles, name=config["roles"]["ranks"])
    poons = utils.get(guild.roles, name=config["roles"]["poons"])
    other = utils.get(guild.roles, name=config["roles"]["other"])
    logging.info("Global Roles Set")


class AdminSys(commands.Cog, name="AdminSystems"):
    """Automated Administration Systems"""

    def __init__(self, bot: BOKBot):
        self.bot = bot
        self.scheduled_good_morning.start()

    # EVENTS:

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id == self.bot.config["administration"]["forbidden"]:
            self.bot.dispatch("trap_sprung", message)

    @commands.Cog.listener()
    async def on_trap_sprung(self, message: Message):
        # Trap is sprung, get all the data needed and validate things.
        guild = message.guild
        if guild is None:
            logging.error("Trap Sprung: Guild is None")
            raise GuildNotFoundError("Guild is None")
        member = message.author
        if isinstance(member, User):
            member = guild.get_member(member.id)
            if member is None:
                logging.error("Trap Sprung: Member is None")
                return
        private_channel = Validators.validate_channel(
            guild.get_channel(self.bot.config["administration"]["private"])
        )

        jail_role = utils.get(guild.roles, name=self.bot.config["roles"]["jail"])
        if jail_role is None:
            logging.error("Trap Sprung: Jail role not found")
            return
        jail_channel = guild.get_channel(self.bot.config["administration"]["jail"])
        Validators.validate_channel(jail_channel, "Trap Sprung")
        jail_log_channel = Validators.validate_channel(
            guild.get_channel(self.bot.config["administration"]["jail_log"]),
            "Trap Sprung",
        )
        officer_role = utils.get(guild.roles, name=self.bot.config["roles"]["admin"])
        if officer_role is None:
            logging.error("Trap Sprung: Admin role not found")
            return

        # Gather up user data and then jail them.
        user_roles = ", ".join(role.name for role in member.roles)
        for role in member.roles:
            await member.remove_roles(role)
        await member.add_roles(jail_role)
        await private_channel.send(
            f"{member.mention} you are imprisoned here for posting in the forbidden channel pending review by {officer_role.mention}"
        )
        await jail_log_channel.send(
            f"{member.mention} has been jailed for posting in the forbidden channel.\nRoles removed: {user_roles}"
        )

        # Fetch all messages from past hour from the author and purge them
        time_delta = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=1
        )
        messages: list[Message] = []

        # Text and Voice-Text channels
        for channel in guild.text_channels + guild.voice_channels:
            try:
                async for msg in channel.history(after=time_delta, limit=None):
                    if msg.author == member:
                        messages.append(msg)
            except discord.Forbidden:
                continue

            for message in messages:
                await message.delete()
            self.bot.jail_count += 1
            self.bot.librarian.put_jail(self.bot.jail_id, self.bot.jail_count)

    @commands.Cog.listener()
    async def on_ready(self):
        gather_roles(self.bot.get_guild(self.bot.config["guild"]), self.bot.config)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild is None:
            logging.error("Member Join: Guild is None")
            raise GuildNotFoundError("Member Join: Guild is None")
        if self.bot.config["roles"]["default"] != "none":
            await member.add_roles(default, ranks, poons, other)
            logging.info(
                f"Added Roles: {str(default)}, {str(ranks)}, {str(poons)}, {str(other)} to: {member.display_name}"
            )
        await guild.system_channel.send(
            f"Welcome {member.mention} to Breath Of Kynareth! Winds of Kyne be with you!\n"
            f"Please read the rules in <#847968244949844008> and follow the directions for "
            f"access to the rest of the server.\n"
            f"Once you do be sure to check out how to get ranked in <#933821777149329468>\n"
            f"If something seems wrong just ping the Storm Bringers."
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        private_channel = member.guild.get_channel(
            self.bot.config["administration"]["private"]
        )
        to_send = ""
        rank_data = self.bot.librarian.get_rank(member.id)
        count_data = self.bot.librarian.get_count(member.id)
        try:
            rosters_removed = []
            channel_name = ""
            user_id = f"{member.id}"
            to_send += f"{member.name} - {member.display_name} has left the server\n"
            for i in self.bot.rosters:
                if isinstance(self.bot.rosters[i], Roster):
                    _, role, is_on = self.bot.rosters[i].remove_member(user_id, True)
                    if is_on:
                        channel_name = getattr(
                            self.bot.get_channel(int(i)), "name", "Unknown Channel"
                        )
                        logging.info(
                            f"Updating Roster {channel_name} for member removal"
                        )
                        self.bot.librarian.put_roster(i, self.bot.rosters[i])
                        rosters_removed.append(f"{channel_name} - {role}")
                elif isinstance(self.bot.rosters[i], EventRoster):
                    if user_id in self.bot.rosters[i].members.keys():
                        channel_name = getattr(
                            self.bot.get_channel(int(i)), "name", "Unknown Channel"
                        )
                        self.bot.rosters[i].remove_member(user_id)
                        rosters_removed.append(channel_name)
                        logging.info(
                            f"Updating Roster {channel_name} for member removal"
                        )
                        self.bot.librarian.put_roster(i, self.bot.rosters[i])

            # Purge Data
            self.bot.librarian.delete_default(member.id)
            self.bot.librarian.delete_rank(member.id)
            self.bot.librarian.delete_count(member.id)
            self.bot.librarian.delete_birthday(member.id)

            to_send = embed_factory.EmbedFactory.create_member_leave_embed(
                count_data, rank_data, member, rosters_removed, self.bot.language
            )
            await private_channel.send(embed=to_send)
        except Exception as e:
            await private_channel.send("Unable to delete Member data")
            logging.exception(f"Member Remove Error: {str(e)}")

    @commands.Cog.listener()
    async def on_weekly_purge(self):
        try:
            # Cleanup Undo Data'
            self.bot.librarian.delete_many_undo_data(
                datetime.datetime.now(datetime.timezone.utc)
            )
        except Exception as e:
            private_channel = self.bot.get_channel(
                self.bot.config["administration"]["private"]
            )
            await private_channel.send(
                "Unable to apply initial role and/or welcome the new user"
            )
            logging.exception(f"Member Join Error: {str(e)}")

    # AUTOMATED TASKS
    @tasks.loop(time=scheduled_time)
    async def scheduled_good_morning(self):
        try:
            if time.localtime().tm_isdst == 0:
                await asyncio.sleep(3600)
            guild = self.bot.get_guild(self.bot.config["guild"])
            channel = guild.get_channel(self.bot.config["morning_channel"])
            await channel.send(self.bot.config["morning"])
            lost_members = [375768932377952257, 504470891972001803]
            main_message = "Happy Anniversary!"
            lost_message = "Happy Anniversary, we miss you buddy."
            try:
                today = datetime.datetime.today()
                today_month = today.month
                today_day = today.day
                today_year = today.year
                birthday_str = f"{today_month}/{today_day}"
                if birthday_str == "5/4":
                    await channel.send(
                        "Happy BOKiversary to everyone! May the winds of Kyne be with you!"
                    )
                for member in guild.members:
                    if any(
                        self.bot.config["roles"]["default"] in role.name
                        for role in member.roles
                    ):
                        continue
                    joined = member.joined_at
                    joined_month = joined.month
                    joined_day = joined.day
                    joined_year = joined.year
                    if (
                        today_month == joined_month
                        and today_day == joined_day
                        and today_year > joined_year
                    ):
                        await channel.send(
                            f"{member.mention} {lost_message if member.id in lost_members else main_message}"
                        )
                if birthday_str == "11/19":
                    await channel.send(
                        "Happy Birthday to me! May the codebase grow just as we all do!"
                    )
                birthdays = self.bot.librarian.get_birthdays(birthday_str)
                if birthdays:
                    for b in birthdays:
                        member = guild.get_member(int(b))
                        if member:
                            await channel.send(f"{member.mention} Happy Birthday!")
                if birthday_str == "2/28":
                    if calendar.isleap(today_year):
                        return
                    leap_birthdays = self.bot.librarian.get_birthdays("2/29")
                    if leap_birthdays:
                        for b in leap_birthdays:
                            member = guild.get_member(int(b))
                            if member:
                                await channel.send(
                                    f"{member.mention} Happy Leap Birthday!"
                                )
                if today.weekday() == 6:  # Sunday
                    self.bot.dispatch("on_weekly_purge")

            except Exception as e:
                await channel.send("Unable to get the Anniversaries.")
                logging.exception(f"Good Morning Task Anniversary Error: {str(e)}")
        except Exception as e:
            logging.exception(f"Good Morning Task Error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(AdminSys(bot))
