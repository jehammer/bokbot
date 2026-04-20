from bot.models import Roster
from discord.ui import Modal, TextInput
from discord import Interaction, TextStyle
from bot.services import Utilities
import logging


class FillModal(Modal):
    def __init__(self, interaction: Interaction, bot, user_language, channel_id):
        self.user_language = user_language
        self.bot = bot
        self.ui = self.bot.language[user_language]["ui"]["Fill"]
        self.lang = self.bot.language[user_language]["replies"]
        self.channel_id = channel_id
        self.channel = interaction.guild.get_channel(int(self.channel_id))
        super().__init__(title=f"{self.ui['Title']}")
        self.initialize()

    def initialize(self):
        self.confirm = TextInput(
            label=f"{self.ui['Label'] % self.channel.name}",
            placeholder=f"{self.ui['Placeholder']}",
            style=TextStyle.short,
            required=True,
        )
        self.add_item(self.confirm)

    async def on_submit(self, interaction: Interaction):
        val = self.confirm.value.strip().lower()
        if val != "y" and val != "n":
            await interaction.response.send_message(
                f"{self.lang['Fill']['InvalidInput']}"
            )
            return
        if val != "y":
            await interaction.response.send_message(f"{self.lang['Fill']['NInput']}")
            return

        result = self.bot.rosters[self.channel_id].fill_spots()
        if result:
            self.bot.librarian.put_roster(
                self.channel_id, self.bot.rosters[self.channel_id]
            )
            await interaction.response.send_message(
                f"{self.bot.language[self.user_language]['replies']['Fill']['Filled']
                                                       % self.channel.name}"
            )
        else:
            await interaction.response.send_message(
                f"{Utilities.format_error(user_language, self.bot.language[self.user_language]['replies']['Fill']['NotFilled'])}"
            )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.bot.language[self.user_language]['replies']['Unknown'])}"
        )
        logging.error(f"Roster Fill Error: {str(error)}")
        return
