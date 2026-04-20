from discord.ext import commands
import logging
import random
from bot.models import BOKBot
from bot.services import Utilities

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class Shames(commands.Cog, name="Shames"):
    """See peoples shames"""

    def __init__(self, bot: BOKBot):
        self.bot = bot

    @commands.command(name="vundees")
    async def vundees_moment(self, ctx: commands.Context):
        """He splooged."""
        try:
            await ctx.send(
                "https://media.discordapp.net/attachments/911730032286785536/911730140604678204/Vundees.gif"
            )
        except Exception as e:
            await ctx.send("Unable to send image")
            logging.error("Vundees error: " + str(e))

    @commands.command(name="lost")
    async def lost(self, ctx: commands.Context):
        """Then he was lost!"""
        await ctx.send(
            "https://media.discordapp.net/attachments/911730032286785536/975825818506903562/Lost_died.gif"
        )

    @commands.command(name="arma")
    async def get_arma_moment(self, ctx: commands.Context, choice=None):
        """Arma Moments"""
        user_language = Utilities.get_language(ctx.author)
        try:
            ran = int(choice) if choice is not None else random.randint(1, 3)
            match ran:
                case 1:
                    await ctx.send(
                        "https://media.discordapp.net/attachments/911730032286785536/911730134044794930/Arma.gif"
                    )
                case 2:
                    await ctx.send("https://youtu.be/NdySJq7lG44")
                case 3:
                    await ctx.send(
                        "https://cdn.discordapp.com/attachments/911730032286785536/1443376086405615668/ByeByeTZC.png"
                    )
                case _:
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['BadNumber'])}"
                    )
        except Exception as e:
            await ctx.send("Unable to send image")
            logging.error("Arma error: " + str(e))

    @commands.command(name="drak")
    async def get_drak_moment(self, ctx: commands.Context, choice=None):
        """Drak Moment"""
        user_language = Utilities.get_language(ctx.author)
        try:
            ran = int(choice) if choice is not None else random.randint(1, 3)
            match ran:
                case 1:
                    await ctx.send(
                        "https://media.discordapp.net/attachments/911730032286785536/911730136628461589/Drak.gif"
                    )
                case 2:
                    await ctx.send("https://youtu.be/jv2HiOn7C5A")
                case 3:
                    await ctx.send(
                        "https://cdn.discordapp.com/attachments/911730032286785536/1245114737939841024/must_grow.png"
                    )
                case _:
                    await ctx.reply(
                        f"{Utilities.format_error(user_language, self.bot.language[user_language]['replies']['BadNumber'])}"
                    )

        except Exception as e:
            await ctx.send("Unable to send gif")
            logging.error("Drak error: " + str(e))

    @commands.command(name="bever")
    async def bever_moment(self, ctx: commands.Context):
        """Bever stuff"""
        try:
            await ctx.send(
                "https://media.discordapp.net/attachments/911730032286785536/987806807386894336/Bever.png"
            )
        except Exception as e:
            await ctx.send("Unable to send the image")
            logging.error(f"Bever error: {str(e)}")

    @commands.command(name="auddy")
    async def auddy_moment(self, ctx: commands.Context):
        """It tickled the snoot"""
        try:
            await ctx.send(
                "https://media.discordapp.net/attachments/911730032286785536/911730135034646558/Auddy.gif"
            )
        except Exception as e:
            await ctx.send("Unable to send the gif")
            logging.error(f"Auddy error: {str(e)}")

    @commands.command(name="rng")
    async def rng(self, ctx: commands.Context):
        """RNG In vAA HM"""
        await ctx.send(
            "https://media.discordapp.net/attachments/911730032286785536/911730139770019921/RNG.gif"
        )

    @commands.command(name="kiwa")
    async def kiwa_moment(self, ctx: commands.Context):
        """Yee'd Her Haw"""
        try:
            await ctx.send(
                "https://cdn.discordapp.com/attachments/911730032286785536/1443374376631275521/Kiwa.png"
            )
        except Exception as e:
            await ctx.send("Unable to send the image")
            logging.error(f"Kiwa error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(Shames(bot))
