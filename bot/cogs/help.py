import logging
import discord
import yaml
from discord.ext import commands
from bot.models import BOKBot
from bot.services import Utilities
from difflib import ndiff

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s: %(message)s',
    handlers=[
        logging.FileHandler('log.log', mode='a'),
        logging.StreamHandler()
    ])  # , datefmt="%Y-%m-%d %H:%M:%S")

mapping = None


async def send_embed(ctx, embed):
    try:
        await ctx.send(embed=embed)
    except Exception as e:
        logging.error(f"Help Embed Send Error: {str(e)}")


def load_mapping():
    with open("languages/mapping.yaml", 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    logging.info(f"Translate Error Mapping Loaded")
    return data_loaded


class Helpers(commands.Cog):
    """Commands for Bot help and more"""

    def __init__(self, bot):
        self.bot = bot
        global mapping
        mapping = load_mapping()

    @commands.command(name='intro')
    async def send_welcome_intro(self, ctx: commands.Context):
        pass

    @commands.command(name='translate')
    async def translate_error(self, ctx: commands.Context):
        """Translates BOKBot Error to your language"""
        lang = Utilities.get_language(ctx.author)
        try:
            ref = ctx.message.reference
            # Check if it is a reply or not
            if ref is None:
                await ctx.reply(Utilities.format_error(lang, self.bot.language[lang]['replies']['Help']['NotReply']))
                return

            message = await ctx.fetch_message(ref.message_id)
            sent_message = message.content

            # Strip out the codes and get the lang stuff
            error_code = sent_message[:5]
            lang_code = int(error_code[0])
            error_code = error_code[-4:]
            og_lang = Utilities.get_language_from_number(lang_code)

            global mapping
            unpacked = mapping[error_code].split(',')
            if len(unpacked) == 1:
                # Top-Level Error
                main = unpacked[0]
                error = self.bot.language[lang]['replies'][main]
                og_lang_error = self.bot.language[og_lang]['replies'][main]
            else:
                main = unpacked[0]
                sub = unpacked[1]
                error = self.bot.language[lang]['replies'][main][sub]
                og_lang_error = self.bot.language[og_lang]['replies'][main][sub]

            # Error fixing - if there is no %s formatting needed then just reply with the translated error.
            if '%s' in error:
                # Strip out the error number portion of each
                sent_message = sent_message[6:]
                og_lang_error = og_lang_error[5:]

                # Compare the two and get the missing bits
                diff = ndiff(sent_message.split(), og_lang_error.split())
                diffs = [line for line in diff if line.startswith('- ') or line.startswith('+ ')]
                missing = [line[2:] for line in diffs if line.startswith('- ')]

                # Join the missing bits into strings
                added = ''.join(missing).replace('`', '')

                # Format the error and send it back
                error = error % added
            await ctx.reply(Utilities.format_error(lang, error))

        except (ValueError, KeyError) as e:
            logging.error(f"Translate Error: {str(e)}")
            await ctx.reply(Utilities.format_error(lang, self.bot.language[lang]['replies']['Help']['NotReply']))


    @commands.command(name="help")
    async def help(self, ctx, *input):
        """Help system of BOKBot"""

        # TODO: Replace with new help yaml file.

        user_language = Utilities.get_language(ctx.author)

        # Temporarily use English as no other language is available yet

        try:
            # TODO:
            #   First: Check if it is a Cog
            #       Post all commands with their short name
            #   Second: Check if it is a command
            #       Use the long unless None then use the short

            # checks if cog parameter was given
            # if not: sending all modules and commands not associated with a cog
            pages = None
            if not input:

                # starting to build embed
                emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                                    description=f'Use `!help <module>` to gain more information about that module\n'
                                                f'Be sure to check <#932438565009379358> for more in-depth help!')

                # iterating trough cogs, gathering descriptions
                cogs_desc = ''
                for cog in self.bot.cogs:
                    cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

                # adding 'list' of cogs to embed
                emb.add_field(name='Modules', value=cogs_desc, inline=False)

                # integrating trough uncategorized commands
                commands_desc = ''
                for command in self.bot.walk_commands():
                    # if cog not in a cog
                    # listing command if cog name is None and command isn't hidden
                    if not command.cog_name and not command.hidden:
                        commands_desc += f'{command.name} - {command.help}\n'

                # adding those commands to embed
                if commands_desc:
                    emb.add_field(name='Not belonging to a module', value=commands_desc, inline=False)

                # setting information about author
                emb.add_field(name="About",
                              value=f"BOKBot is Developed by Drakador, for any and all support about it feel\n "
                                    f"free to ask in chat or ping him.")
                emb.set_footer(text=f"Thank you for using BOKBot")

            # block called when one cog-name is given
            # trying to find matching cog and it's commands
            elif len(input) == 1:
                found = False
                # iterating through cogs
                for cog in self.bot.cogs:
                    # check if cog is the matching one
                    if cog.lower() == input[0].lower():

                        # making title - getting description from doc-string below class
                        page = discord.Embed(title=f'{cog} - Commands', description=self.bot.cogs[cog].__doc__,
                                             color=discord.Color.green())

                        page.add_field(name="", value="Use `!help <command>` for specific command information",
                                       inline=False)

                        next_page = discord.Embed(title=f'{cog} - Commands (Cont)',
                                                  description=self.bot.cogs[cog].__doc__,
                                                  color=discord.Color.green())

                        # getting commands from cog
                        count = 0
                        pages = []

                        for command in self.bot.get_cog(cog).get_commands():
                            # if cog is not hidden
                            if not command.hidden:
                                if count == 24:
                                    pages.append(page)
                                    count = 0
                                    page = next_page
                                else:
                                    page.add_field(name=f"", value=f"`!{command.name}`\t{command.help}", inline=False)
                                count += 1
                        for command in self.bot.get_cog(cog).get_app_commands():
                            if count == 24:
                                pages.append(page)
                                count = 0
                                page = next_page
                            else:
                                page.add_field(name=f"", value=f"`/{command.name}`\t{command.description}",
                                               inline=False)
                            count += 1
                        pages.append(page)
                        # found cog - breaking loop
                        found = True
                        break

                # It is a command in a cog, iterate through and find the specific command within the cog
                if found is False:
                    for cog in self.bot.cogs:
                        for command in self.bot.get_cog(cog).get_commands():
                            if command.name.lower() == input[0].lower() or input[0].lower() in command.aliases:
                                if not command.hidden:
                                    # Check for aliases or not aliases
                                    if len(command.aliases) > 0:
                                        aliases = ""
                                        for alias in command.aliases:
                                            aliases += alias + ", "
                                        aliases = aliases[:-2]  # Cut off the last comma and whitespace
                                        emb = discord.Embed(title=f'{cog}: !{command} - aliases: {aliases}',
                                                            color=discord.Color.blurple())
                                    else:
                                        emb = discord.Embed(title=f'{cog}: !{command}', color=discord.Color.blurple())
                                    emb.add_field(name=f"", value=f"{command.help}", inline=False)
                                    # found so break
                                    found = True
                                else:
                                    break
                        if not found:
                            for command in self.bot.get_cog(cog).get_app_commands():
                                if command.name.lower() == input[0].lower():
                                    # Check for aliases or not aliases
                                    emb = discord.Embed(title=f'{cog}: /{command.name}', color=discord.Color.blurple())
                                    emb.add_field(name=f"", value=f"{command.description}", inline=False)
                                    # found so break
                                    found = True
                        if found is True:
                            break

                    # if input not found
                    # yes, for-loops have an else statement, it's called when no 'break' was issued

                    else:
                        emb = discord.Embed(title="Impossible. Perhaps the archives are incomplete?",
                                            description=f"I do not have a module or command called `{input[0]}`",
                                            color=discord.Color.orange())
                        emb.set_image(
                            url='https://media.discordapp.net/attachments/911730032286785536/1073645138506694806/Incomplete.png')

            # too many cogs requested - only one at a time allowed
            elif len(input) > 1:
                emb = discord.Embed(title="That's too much",
                                    description="Please request only one module or command at once",
                                    color=discord.Color.orange())

            else:
                emb = discord.Embed(title="It's a magical place.",
                                    description="I don't know how you got here. By all accounts, this code is unreachable.",
                                    color=discord.Color.red())

            # sending reply embed using our own function defined above
            if pages is not None:
                for i in pages:
                    await send_embed(ctx, i)
            else:
                await send_embed(ctx, emb)
        except Exception as e:
            await ctx.send("I was unable to complete the help command")
            logging.error(f"Help command Error: {str(e)}")


async def setup(bot: BOKBot):
    await bot.add_cog(Helpers(bot))
