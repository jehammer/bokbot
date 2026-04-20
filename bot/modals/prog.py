from discord.ui import Modal, TextInput
from discord import Interaction, TextStyle
import logging
from bot.services import RosterExtended, Utilities

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class ProgModal(Modal):
    def __init__(self, bot, interaction: Interaction, user_language):
        self.config = bot.config
        self.bot = bot
        self.language = bot.language[user_language]["replies"]
        self.ui_language = bot.language[user_language]["ui"]
        super().__init__(title=self.ui_language["Prog"]["Title"])
        self.initialize()

    def initialize(self):
        roles = self.bot.librarian.get_progs()
        default_vals = ""
        if roles is not None:
            for i in roles:
                default_vals += f"{str(i)}\n"
        self.roles_input = TextInput(
            label=self.ui_language["Prog"]["RolesInput"]["Label"],
            placeholder=self.ui_language["Prog"]["RolesInput"]["Placeholder"],
            default=default_vals,
            style=TextStyle.long,
            required=True,
        )
        self.add_item(self.roles_input)

    async def on_submit(self, interaction: Interaction):
        role_list = self.roles_input.value.splitlines()
        logging.info("Updating Prog Role Data")
        self.bot.librarian.put_progs(role_list)
        logging.info("Updated Prog Role Data")
        self.bot.limits = RosterExtended.get_limits(
            librarian=self.bot.librarian, roles_config=self.bot.config["raids"]["ranks"]
        )
        await interaction.response.send_message(self.language["Prog"]["Updated"])

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logging.error(f"Prog Roles Update Error: {str(error)}")
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.language['Incomplete'])}"
        )
