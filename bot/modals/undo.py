from bot.models import Roster, EventRoster
from bot.services import RosterExtended, Utilities, EmbedFactory
from discord import Interaction, TextStyle, Role
from discord.utils import get
from discord.ui import TextInput, Modal
import copy
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class UndoModal(Modal):
    def __init__(
        self,
        interaction: Interaction,
        bot,
        users_language,
        roster: Roster | EventRoster,
        roster_name,
    ):
        self.bot = bot
        self.language = bot.language[users_language]["replies"]["Undo"]
        self.ui = bot.language[users_language]["ui"]["Undo"]
        self.channel = None
        self.channel_id = None
        self.user_language = users_language
        self.roster = roster
        self.channel_name = roster_name
        super().__init__(title=f"{self.ui['Title'] % roster_name}")
        self.initialize()

    def initialize(self):
        self.confirm = TextInput(
            label=f"{self.ui['Confirm']['Label']}",
            default="",
            placeholder=f"{self.ui['Confirm']['Placeholder']}",
            style=TextStyle.short,
            required=True,
        )
        self.add_item(self.confirm)

    async def on_submit(self, interaction: Interaction):
        try:
            confirm_value = self.confirm.value.strip().lower()
            if confirm_value != "y":
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.language['BadConfirmError'])}"
                )
                return

            pingable = None
            name_val = ""
            if isinstance(self.roster, Roster):
                pingable = RosterExtended.create_pingable_role_name(
                    trial=self.roster.trial,
                    date=self.roster.date,
                    tz=self.bot.config["raids"]["timezone"],
                    guild=interaction.guild,
                )
                name_val = self.roster.trial
            elif isinstance(self.roster, EventRoster):
                pingable = RosterExtended.create_pingable_role_name(
                    trial=self.roster.event,
                    date=self.roster.date,
                    tz=self.bot.config["raids"]["timezone"],
                    guild=interaction.guild,
                )
                name_val = self.roster.event

            role: Role = await interaction.guild.create_role(
                name=pingable, mentionable=True
            )
            self.roster.pingable = role.id

            new_name = RosterExtended.generate_channel_name(
                self.roster.date, name_val, self.bot.config["raids"]["timezone"]
            )
            category = interaction.guild.get_channel(
                self.bot.config["raids"]["category"]
            )
            self.channel = await category.create_text_channel(new_name)
            self.channel_id = self.channel.id

            self.bot.rosters[self.channel.id] = copy.deepcopy(self.roster)
            self.bot.librarian.put_roster(
                channel_id=self.channel_id, data=self.bot.rosters[self.channel.id]
            )
            self.bot.librarian.delete_undo_data(self.channel_name)

            guild = interaction.guild
            embed = None
            if isinstance(self.roster, Roster):
                if isinstance(self.bot.limits[self.roster.role_limit], list):
                    # Need to work with 3 roles to check, dps | tank | healer order
                    limiter_dps = get(
                        guild.roles, name=self.bot.limits[self.roster.role_limit][0]
                    )
                    limiter_tank = get(
                        guild.roles, name=self.bot.limits[self.roster.role_limit][1]
                    )
                    limiter_healer = get(
                        guild.roles, name=self.bot.limits[self.roster.role_limit][2]
                    )

                    roles_req = f"{limiter_dps.mention} {limiter_tank.mention} {limiter_healer.mention}"
                else:
                    limiter = get(
                        guild.roles, name=self.bot.limits[self.roster.role_limit]
                    )
                    roles_req = f"{limiter.mention}"

                embed = EmbedFactory.create_status(
                    roster=self.roster,
                    language=self.bot.language[self.user_language]["ui"]["Status"],
                    bot=self.bot,
                    roles_req=roles_req,
                    guild=guild,
                )

            elif isinstance(self.roster, EventRoster):
                embed = EmbedFactory.create_event_roster(
                    roster=self.roster,
                    language=self.user_language,
                    bot=self.bot,
                    guild=guild,
                )

            await self.channel.send(embed=embed)

            await interaction.response.send_message(
                f"{self.language['Completed'] % self.channel.name}"
            )

        except Exception as e:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.language['CantCreate'])}"
            )
            logging.error(f"Undo Creation Channel And Embed Error: {str(e)}")

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.bot.language['Unknown'])}"
        )
        logging.error(f"Undo Error: {str(error)}")
