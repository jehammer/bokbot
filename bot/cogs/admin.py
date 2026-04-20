import discord
from discord import Member, FFmpegPCMAudio
from discord.ext import commands, tasks
import logging
import asyncio

from gtts import gTTS

from bot import decor as permissions
import datetime
import shutil
import re
import yaml
import os
import time
import calendar

from bot.models import Roster, EventRoster
from bot.models import BOKBot
from bot.services import Utilities

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

# alert_channel = self.bot.get_guild(self.bot.config['guild']).get_channel(self.bot.config['private'])
# await alert_channel.send(f"Saving Roster or Map error encountered: {str(e)}")


def gather_roles(guild, config):
    """Loads the starting roles for people when joining"""
    global default
    global ranks
    global poons
    global other
    default = discord.utils.get(guild.roles, name=config["roles"]["default"])
    ranks = discord.utils.get(guild.roles, name=config["roles"]["ranks"])
    poons = discord.utils.get(guild.roles, name=config["roles"]["poons"])
    other = discord.utils.get(guild.roles, name=config["roles"]["other"])
    logging.info(f"Global Roles Set")


class Admin(commands.Cog, name="Admin"):
    """Receives Administration commands"""

    def __init__(self, bot: BOKBot):
        self.bot = bot
        self.scheduled_good_morning.start()

    @commands.command(name="nobirthday")
    async def remove_users_birthday(self, ctx: commands.Context):
        """Removes a user's birthday from the database"""
        user_language = Utilities.get_language(ctx.author)
        try:
            self.bot.librarian.delete_birthday(ctx.author.id)
            await ctx.reply(
                f"{self.bot.language[user_language]['replies']['Birthday']['Deleted']}"
            )
        except Exception as e:
            await ctx.reply(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Remove Birthday Error: {str(e)}")

    @commands.command(name="servers", hidden=True)
    @permissions.creator_only()
    async def servers(self, ctx: commands.Context):
        """Check the servers the bot is active in, Owner only"""
        if ctx.message.author.id == self.bot.config["creator"]:
            try:
                all_servers = list(self.bot.guilds)
                allowed_servers = self.bot.config["allowed"]
                await ctx.send(f"Connected on {str(len(all_servers))} servers:")
                await ctx.send("\n".join(guild.name for guild in all_servers))
                for i in all_servers:
                    if i.id not in allowed_servers:
                        await ctx.send(f"Server {i.name} is not allowed.")
            except Exception as e:
                logging.error(f"Server Check Error: {str(e)}")
        else:
            await ctx.send("You do not have permission to do that.")

    @commands.command(name="leaveservers", hidden=True)
    @permissions.creator_only()
    async def leave_bad_servers(self, ctx: commands.Context):
        """Leave false servers, Owner only"""
        if ctx.message.author.id == self.bot.config["creator"]:
            try:
                all_servers = list(self.bot.guilds)
                allowed_servers = self.bot.config["allowed"]
                message = f"<@everyone> COMMON PEASANTRY! YOUR ATTEMPTED THEFT OF ME IS NOT UNNOTICED AND WILL NOT GO UNPUNISHED!"
                for i in all_servers:
                    if i.id not in allowed_servers:

                        members = i.members
                        for m in members:
                            if m.id in ctx.guild.members:
                                await ctx.send(f"{m.name} is also in this server")

                        await ctx.send(f"Leaving Server {i.name}")
                        left = False
                        tried_system = False
                        while not left:
                            if tried_system:
                                for channel in i.text_channels:
                                    try:
                                        await channel.send(message)
                                        await i.leave()
                                        left = True
                                        break
                                    except Exception as e:
                                        logging.info(f"Leaving: {str(e)}")
                                        continue
                            else:
                                try:
                                    channel = i.system_channel
                                    if channel:
                                        await channel.send(message)
                                        await i.leave()
                                        left = True
                                        break
                                    else:
                                        tried_system = True
                                except Exception as e:
                                    logging.info(f"Leaving: {str(e)}")
                                    tried_system = True
                        if not left:
                            await i.leave()
            except Exception as e:
                logging.error(f"Server Check Error: {str(e)}")
        else:
            await ctx.send("You do not have permission to do that.")

    @commands.command(name="shutdown")
    @permissions.creator_only()
    async def shutdown(self, ctx: commands.Context):
        """Shut down the bot, Owner only"""
        try:
            log_name = "log.log"
            date = datetime.datetime.now().strftime("%m-%d-%Y")
            time = datetime.datetime.now().strftime("%I:%M:%S %p")
            logging.info(f"Shutdown command received - {time} on {date}")
            logging.shutdown()
            self.scheduled_good_morning.stop()
            if os.path.exists(log_name):
                file_name = f"log-{date}.log"
                os.makedirs("logs", exist_ok=True)
                version = 1
                while os.path.exists(os.path.join("logs", file_name)):
                    base_name, extension = os.path.splitext(file_name)
                    base_name = re.sub(r"\(\d{1,2}\)", "", base_name)
                    file_name = f"{base_name}({version}){extension}"
                    version += 1
                path = os.path.join("logs", file_name)
                shutil.move(log_name, path)
            await self.bot.close()
        except Exception as e:
            logging.error(f"Shutdown Error: {str(e)}")

    @commands.command(name="getarma")
    @permissions.has_officer()
    async def get_arma(self, ctx: commands.Context):
        """Gets Arma with a series of DMs and pings in case he forgets again"""
        try:
            arma = ctx.message.guild.get_member(self.bot.config["arma"])
            if arma:
                for i in range(4):
                    await arma.send("It is time for your regularly scheduled event")
                    await ctx.send(arma.mention + " it is time for you to get on!")
                    await asyncio.sleep(0.5)

            else:
                await ctx.send("Cannot find Arma")
        except Exception as e:
            await ctx.send("I cannot call Arma")
            logging.error(f"Call Arma error: {str(e)}")

    @commands.command(name="sr", hidden=True)
    @permissions.creator_only()
    async def send_message_into_chat(self, ctx: commands.Context):
        """Just a fun little thing"""
        try:
            msg = ctx.message.content
            msg = msg.split(" ", 2)
            guild = self.bot.get_guild(self.bot.config["guild"])
            channel = guild.get_channel(int(msg[1]))
            await channel.send(msg[2])
        except Exception as e:
            await ctx.send("Unable to send the message")
            logging.error(f"sr error: {str(e)}")

    @commands.command(name="vr", hidden=True)
    @permissions.creator_only()
    async def send_voice_into_vc(self, ctx: commands.Context):
        """Just a fun little thing for voice"""
        try:
            msg = ctx.message.content
            msg = msg.split(" ", 2)
            guild = self.bot.get_guild(self.bot.config["guild"])
            channel = guild.get_channel(int(msg[1]))
            tts = gTTS(msg[2], lang="en")
            tts.save("voice.mp3")
            voice = await channel.connect()
            source = FFmpegPCMAudio("voice.mp3")
            voice.play(source)
            while voice.is_playing():
                await asyncio.sleep(2)
            await voice.disconnect()

        except Exception as e:
            await ctx.send("Unable to complete")
            logging.error(f"sr error: {str(e)}")

    @commands.command(name="cogreload", aliases=["reload", "reloadcog"])
    @permissions.creator_only()
    async def reload_cogs(self, ctx: commands.Context):
        """Owner Only: Reloads the cogs following an update"""
        try:
            logging.info(f"Stopping tasks")
            self.scheduled_good_morning.cancel()
            logging.info(f"Stopped tasks")
            logging.info("Preparing to reload cogs")
            for filename in os.listdir("cogs"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    try:
                        await self.bot.unload_extension(f"cogs.{filename[:-3]}")
                        logging.info(f"Successfully unloaded {filename}")

                    except Exception as e:
                        logging.info(f"Failed to unload {filename}")
                        logging.error(f"Cog Unload error: {str(e)}")

            logging.info(f"Reloading Cogs after unload")
            for filename in os.listdir("cogs"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    try:
                        await self.bot.load_extension(f"cogs.{filename[:-3]}")
                        logging.info(f"Successfully loaded {filename}")

                    except Exception as e:
                        logging.info(f"Failed to load {filename}")
                        logging.error(f"Cog Load error: {str(e)}")
            logging.info(f"Cog Reload completed")
            self.bot.dispatch("load_on_ready", self.bot)
            await ctx.send(f"Cog Reload completed")
        except Exception as e:
            logging.error(f"Cog Reload Error: {str(e)}")
            await ctx.send(
                f"There was an issue reloading the cogs, check the logs for more info."
            )

    @commands.command(
        name="config",
        aliases=["configreload", "reset", "configreset", "resetconfig", "reloadconfig"],
    )
    @permissions.creator_only()
    async def reload_config(self, ctx: commands.Context):
        """Owner Only: Reloads the config following an update"""
        try:
            logging.info(f"Loading new config")
            with open("config.yaml", "r") as stream:
                data_loaded = yaml.safe_load(stream)
            self.bot.config = data_loaded
            logging.info(f"New config loaded")
            await ctx.send(f"Config loaded")
        except Exception as e:
            logging.error(f"Config Reload Error: {str(e)}")
            await ctx.send(
                f"There was an issue reloading the config, check the logs for more info."
            )

    @commands.command(name="sync", aliases=["resync", "synchronize", "rescynchronize"])
    @permissions.creator_only()
    async def sync_application_commands(self, ctx: commands.Context):
        """Owner Only: Force Syncs Application Commands"""
        try:
            synced = await self.bot.tree.sync()
            logging.info(f"Synced {len(synced)} command(s)")
            await ctx.send(f"Sync Complete. Synced {len(synced)} Application Commands.")
        except Exception as e:
            logging.error(f"Sync Error: {str(e)}")
            await ctx.send(f"There was an issue syncing, check the logs for more info.")

    @commands.command(
        name="trial",
        aliases=[
            "date",
            "datetime",
            "time",
            "leader",
            "change",
            "rolenum",
            "memo",
            "limit",
            "call",
            "modify",
            "fill",
            "close",
            "runcount",
            "remove",
            "add",
            "rank",
            "kowtow",
        ],
        hidden=True,
    )
    async def old_commands_alert(self, ctx: commands.Context):
        user_language = Utilities.get_language(ctx.author)
        now_modify = [
            "date",
            "datetime",
            "time",
            "leader",
            "change",
            "rolenum",
            "memo",
            "limit",
        ]
        if ctx.invoked_with in now_modify:
            new_command = "modify"
        else:
            new_command = ctx.invoked_with
        await ctx.reply(
            f"{self.bot.language[user_language]['replies']['MovedAnswer'] % new_command}"
        )

    # EVENTS:

    @commands.Cog.listener()
    async def on_ready(self):
        gather_roles(self.bot.get_guild(self.bot.config["guild"]), self.bot.config)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            guild = member.guild
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
        except Exception as e:
            private_channel = guild.get_channel(
                self.bot.config["administration"]["private"]
            )
            await private_channel.send(
                "Unable to apply initial role and/or welcome the new user"
            )
            logging.error(f"Member Join Error: {str(e)}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        private_channel = member.guild.get_channel(
            self.bot.config["administration"]["private"]
        )
        to_send = ""
        rank_data = self.bot.librarian.get_rank(member.id)
        count_data = self.bot.librarian.get_count(member.id)
        try:
            was_on = False
            channel_name = ""
            user_id = f"{member.id}"
            to_send += f"{member.name} - {member.display_name} has left the server\n"
            for i in self.bot.rosters:
                if isinstance(self.bot.rosters[i], Roster):
                    _, role, is_on = self.bot.rosters[i].remove_member(user_id, True)
                    if is_on:
                        was_on = True
                        channel_name = getattr(
                            self.bot.get_channel(int(i)), "name", "Unknown Channel"
                        )
                        logging.info(
                            f"Updating Roster {channel_name} for member removal"
                        )
                        self.bot.librarian.put_roster(i, self.bot.rosters[i])
                        to_send += f"Traitor was removed as a {role.capitalize()} from {channel_name}\n"
                elif isinstance(self.bot.rosters[i], EventRoster):
                    if user_id in self.bot.rosters[i].members.keys():
                        channel_name = getattr(
                            self.bot.get_channel(int(i)), "name", "Unknown Channel"
                        )
                        self.bot.rosters[i].remove_member(user_id)
                        to_send += f"Traitor was removed from {channel_name}\n"
                        was_on = True
                        logging.info(
                            f"Updating Roster {channel_name} for member removal"
                        )
                        self.bot.librarian.put_roster(i, self.bot.rosters[i])

            if was_on:
                to_send += "The Traitor has been removed from all active rosters.\n"
            else:
                to_send += "The Traitor was not on any active rosters.\n"
            # Delete Default
            self.bot.librarian.delete_default(member.id)
            to_send += "Deleted Default\n"

            # Default Ranks
            self.bot.librarian.delete_rank(member.id)
            to_send += "Deleted Ranks\n"

            # Delete Count
            self.bot.librarian.delete_count(member.id)
            to_send += "Deleted Counts\n"

            # Delete Birthday
            self.bot.librarian.delete_birthday(member.id)
            to_send += "Deleted Birthday\n"

            to_send += f"{member.display_name} joined {calendar.month_name[member.joined_at.month]} {member.joined_at.day}{Utilities.suffix(member.joined_at.day)} {member.joined_at.year}\n"
            if count_data is not None:
                to_send += f"{member.display_name} last ran {count_data.lastTrial} on {count_data.lastDate}\n"
            else:
                to_send += f"{member.display_name} has no recorded runs\n"
            if rank_data is not None:
                to_send += (
                    f"{member.display_name} last ranked on {rank_data.last_called}\n"
                )
            else:
                to_send += f"{member.display_name} has no recorded rankings\n"

            await private_channel.send(to_send)
        except Exception as e:
            await private_channel.send("Unable to delete Member data")
            logging.error(f"Member Remove Error: {str(e)}")

    # AUTOMATED TASKS
    @tasks.loop(time=scheduled_time)
    async def scheduled_good_morning(self):
        try:
            if time.localtime().tm_isdst == 0:
                await asyncio.sleep(3600)
            guild = self.bot.get_guild(self.bot.config["guild"])
            channel = guild.get_channel(self.bot.config["morning_channel"])
            await channel.send(self.bot.config["morning"])
            try:
                today = datetime.datetime.today()
                today_month = today.month
                today_day = today.day
                today_year = today.year
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
                        if (
                            member.global_name == "kuvxwb"
                            or member.global_name == "muon.t"
                        ):
                            await channel.send(
                                f"{member.mention} Happy Anniversary, we miss you buddy."
                            )
                        else:
                            await channel.send(f"{member.mention} Happy Anniversary!")
                # TODO: Implement BOKiversary for May 4th each year and BOKBot Birthday in November checks
                birthday_str = f"{today_month}/{today_day}"
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
            except Exception as e:
                await channel.send("Unable to get the Anniversaries.")
                logging.error(f"Good Morning Task Anniversary Error: {str(e)}")
        except Exception as e:
            logging.error(f"Good Morning Task Error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(Admin(bot))
