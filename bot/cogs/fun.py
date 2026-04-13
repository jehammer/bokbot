import calendar
import datetime
import logging
import random
import time
from discord import app_commands, Interaction, Member
from discord.ext import commands

from bot.modals import BirthdayModal
from bot.models import Rank
from bot.services import Utilities, EmbedFactory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class Fun(commands.Cog, name="Fun"):
    """For Fun/Event Type Things"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="fishing")
    async def fishing(self, ctx: commands.Context):
        """Glub Glub"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/1219447029688959067/FishFishes.gif"
        )

    @commands.command(name="jabs")
    async def jabs(self, ctx: commands.Context):
        """The Templars do be like that"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/911837712196173824/jabs.gif"
        )

    @commands.command(name="facepalm")
    async def facepalm(self, ctx: commands.Context):
        """Arma every other second"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/912569604973404160/Facepalm.gif"
        )

    @commands.command(name="fart")
    async def fart(self, ctx: commands.Context):
        """Explosive"""
        await ctx.send(
            "https://media.discordapp.net/attachments/911730032286785536/932433681992278088/Creed.gif"
        )

    @commands.command(name="dungeons")
    async def dungeons(self, ctx: commands.Context):
        """DUNGEONS"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/983363613425278997/dungeons.gif"
        )

    @commands.command(name="bokemon")
    async def bokemon(self, ctx: commands.Context):
        """A link to a perfect song"""
        await ctx.send("https://youtu.be/OZrs7Blmank")

    @commands.command(name="thepull")
    async def thepull(self, ctx: commands.Context):
        """Drak got the thing"""
        await ctx.send("https://youtu.be/Cnf9lRtLSYk")

    @commands.command(name="chainz", aliases=["chains"])
    async def chainz(self, ctx: commands.Context):
        """Just tell him"""
        await ctx.send("https://tenor.com/view/e40-tellmewhentogo-gif-21713338")

    @commands.command(name="logz")
    async def logz(self, ctx: commands.Context):
        """Actual gif of him"""
        await ctx.send("LISTEN HERE SHITHEADS!")
        await ctx.send(
            "https://media.discordapp.net/attachments/911730032286785536/911730138935349308/Logz.gif"
        )

    @commands.command(name="pizza")
    async def pizza_video(self, ctx: commands.Context):
        """Leahs favorite early morning/late night meal."""
        await ctx.send("https://youtu.be/SMkG2FDCQ7w")

    @commands.command(name="ec")
    async def my_ec_gif(self, ctx: commands.Context):
        """You have it!"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/1062132264382775296/DrakadorMyEC.gif"
        )

    @commands.command(name="noec")
    async def no_ec_gif(self, ctx: commands.Context):
        """You don't have it!"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/1062132263980126250/DrakadorNoEC.gif"
        )

    @commands.command(name="noquestionsasked")
    async def no_questions_asked_gif(self, ctx: commands.Context):
        """Absolutely none."""
        await ctx.send("https://tenor.com/view/dont-ask-no-questions-gif-8052545")

    @commands.command(name="cover")
    async def my_bok_cover(self, ctx: commands.Context):
        """Put this over your chat when you stream!"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments/911730032286785536/1219457387640000612/BOK_Stream_Cover.png"
        )

    @app_commands.command(
        name="rank", description="See how much BOKBot approves of you today."
    )
    @app_commands.describe(member="Discord user to rank if not yourself.")
    async def rank_app_command(
        self, interaction: Interaction, member: Member = None
    ) -> None:
        """Ranks someone out of 10000 you ping"""
        user_language = Utilities.get_language(interaction.user)
        try:
            if member is None:
                member = interaction.user
            elif member.bot:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['NoBots'])}"
                )
                return
            user_id = member.id
            rank_data: Rank = self.bot.librarian.get_rank(user_id=user_id)

            if rank_data is None:
                rank_data = Rank()
            timestamp = int(
                time.mktime(datetime.datetime.now().timetuple())
            )  # All this just for a utc timestamp int
            ran = random.randint(1, 10000)
            rank_data.last_called = f"<t:{timestamp}:f>"
            rank_data.count += 1

            # Lowest and Highest check
            if rank_data.lowest > ran:
                rank_data.lowest = ran
            if rank_data.highest < ran:
                rank_data.highest = ran

            listed = [x for x in str(ran)]
            if ran == 69:
                rank_data.six_nine += 1
            elif ran == 420:
                rank_data.four_twenty += 1
            elif ran == 8008:
                rank_data.boob += 1
            elif ran == 314:
                rank_data.pie += 1
            elif ran < 10:
                rank_data.singles += 1
            elif len(set(listed)) <= 1:  # This is single
                rank_data.samsies += 1
            elif len(listed) == 4 and (listed[0] + listed[1] == listed[2] + listed[3]):
                rank_data.doubles += 1
            elif len(listed) == 4 and (
                listed[0] == listed[3] and listed[1] == listed[2]
            ):
                rank_data.palindrome += 1

            self.bot.librarian.put_rank(user_id=user_id, rank_data=rank_data)

            await interaction.response.send_message(
                f"{self.bot.language[user_language]['replies']['Rank']['Generated'] % (member.display_name, f'{ran}{Utilities.suffix(ran)}')}"
            )

        except Exception as e:
            await interaction.response.send_message(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Rank Command Error: {str(e)}")

    @app_commands.command(name="kowtow", description="Check someones Ranking records")
    @app_commands.describe(member="Discord user to check if not yourself.")
    async def send_rank_info_app_command(
        self, interaction: Interaction, member: Member = None
    ) -> None:
        """Prints a leaderboard for your /rank uses"""
        user_language = Utilities.get_language(interaction.user)
        try:
            if member is None:
                member = interaction.user
            elif member.bot:
                await interaction.response.send_message(
                    f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['NoBots'])}"
                )
                return
            user_id = member.id
            rank_data: Rank = self.bot.librarian.get_rank(user_id=user_id)
            if rank_data is None:
                await interaction.response.send_message(
                    f"{self.bot.language[user_language]['replies']['Rank']['NoHistory']}"
                )
                return

            embed = EmbedFactory.create_ranking(
                rank=rank_data,
                lang=self.bot.language[user_language]["ui"]["Rank"],
                name=member.display_name,
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Kowtow Error: {str(e)}")

    @commands.command(name="8ball")
    async def magic_eight_ball(self, ctx: commands.context):
        """Answers a question like a magic 8-ball"""
        # responses from here: https://en.wikipedia.org/wiki/Magic_8-ball#Possible_answers
        ran = random.randint(1, 20)
        response = ""
        match ran:
            case 1:
                response = "It is certain."
            case 2:
                response = "It is decidedly so."
            case 3:
                response = "Without a doubt."
            case 4:
                response = "Yes definitely."
            case 5:
                response = "You may rely on it."
            case 6:
                response = "As I see it, yes."
            case 7:
                response = "Most likely."
            case 8:
                response = "Outlook good."
            case 9:
                response = "Yes."
            case 10:
                response = "Signs point to yes."
            case 11:
                response = "Reply hazy, try again."
            case 12:
                response = "Ask again later."
            case 13:
                response = "Better not tell you now."
            case 14:
                response = "Cannot predict now."
            case 15:
                response = "Concentrate and ask again."
            case 16:
                response = "Don't count on it."
            case 17:
                response = "My reply is no."
            case 18:
                response = "My sources say no."
            case 19:
                response = "Outlook not so good."
            case 20:
                response = "Very doubtful. "
        if ran % 2 == 1:
            ran = random.randint(
                1, 10
            )  # Give this a like 1 in 10 chance of showing up if the number is odd
            if ran == 2:
                response = "Fuck off I am sleeping."

        await ctx.reply(response)

    @commands.command()
    async def goodnight(self, ctx: commands.context):
        """A way to say goodnight to bok"""

        # Wow, this looks ugly, ah well. Say goodnight to the guildies
        message = """
In the great big room
There was a parse dummy backwards in the room
And a merchant buffoon.
And a picture of our first trial clear
And there were there were three little pvpers sitting on chairs
And two little kittens, and even two chickens
And even a Leah, asking for pizza at 1 AM
And a blacksmith and a clothier and a bowl full of alchemy
And a quiet old guild master who was whispering “hush”

Goodnight room
Goodnight moon
Goodnight parse dummy backwards in the room
Goodnight light
And the buffoon
Goodnight pvpers
Goodnight chairs
Goodnight kittens
And goodnight chickens
Goodnight clocks
And goodnight socks
Goodnight Leah
Goodnight blacksmith
And goodnight clothier
Goodnight nobody
Goodnight alchemy
And goodnight to the guild master whispering “hush”
Goodnight stars
Goodnight air
Goodnight noises everywhere
Goodnight BOK
"""
        await ctx.send(message)

    @commands.command(name="otter")
    async def otter(self, ctx: commands.context):
        """An Otterful Greeting!"""
        user_language = Utilities.get_language(ctx.author)
        try:
            await ctx.send(
                "https://cdn.discordapp.com/attachments/911730032286785536/1443359030868447232/otterful.gif "
            )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Otter Error: {str(e)}")

    @commands.command(name="oops")
    async def armas_oops(self, ctx: commands.Context):
        """Self-explanatory"""
        user_language = Utilities.get_language(ctx.author)
        try:
            await ctx.send(
                "https://cdn.discordapp.com/attachments/911730032286785536/1443375553167228989/Oops.png"
            )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Oops error: {str(e)}")

    @commands.command(name="uwu")
    async def lily_uwu(self, ctx: commands.Context):
        """Basically an anime girl"""
        user_language = Utilities.get_language(ctx.author)
        try:
            await ctx.send(
                "https://media.discordapp.net/attachments/911730032286785536/1464875517672161474/Lily.png"
            )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Lily error: {str(e)}")

    @app_commands.command(name="birthday", description="Set your birthday for BOKBot")
    async def set_birthday_app_command(self, interaction: Interaction) -> None:
        """Loads modal to set user birthday"""
        user_language = Utilities.get_language(interaction.user)
        try:
            await interaction.response.send_modal(
                BirthdayModal(
                    interaction=interaction, bot=self.bot, user_lang=user_language
                )
            )

        except Exception as e:
            await interaction.response.send_message(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Birthday Error: {str(e)}")

    @commands.command(name="quickie")
    async def just_a_quick_run(self, ctx: commands.Context):
        """For Octavia"""
        user_language = (
            Utilities.get_language(ctx.author)
            if isinstance(ctx.author, Member)
            else "english"
        )
        try:
            await ctx.send(
                "https://cdn.discordapp.com/attachments/911730032286785536/1492409390052151436/quickie.png"
            )
        except Exception as e:
            await ctx.send(
                f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['Unknown'])}"
            )
            logging.error(f"Quickie error: {str(e)}")


    await bot.add_cog(Fun(bot))
