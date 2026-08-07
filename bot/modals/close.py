from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput
from bot.errors import (
    MissingGuildError,
    MissingInteractionError,
    MissingRoleError,
)
from bot.models.bokbot import BOKBot
from bot.services import Utilities, RosterExtended
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class CloseModal(Modal):
    def __init__(self, interaction: Interaction, bot: BOKBot, lang, channel_id):

        if interaction is None:
            raise MissingInteractionError
        if interaction.guild is None:
            raise MissingGuildError

        self.localization = bot.language[lang]["replies"]
        self.ui_language = bot.language[lang]["ui"]
        self.bot = bot
        self.user_language = lang
        self.config = bot.config
        self.channel_id = channel_id
        self.channel = interaction.guild.get_channel(int(self.channel_id))
        if self.channel is None:
            self.name = self.channel_id
        else:
            self.name = self.channel.name
        super().__init__(title=f"{self.ui_language['Close']['Title']}")
        self.initialize()

    def initialize(self):
        # Add all the items here based on what is above
        self.confirm = TextInput(
            label=f"{self.ui_language['Close']['Confirm']['Label'] % self.name}",
            placeholder=f"{self.ui_language['Close']['Confirm']['Placeholder']}",
            style=TextStyle.short,
            required=True,
        )
        self.runs = TextInput(
            label=f"{self.ui_language['Close']['Runs']['Label']}",
            placeholder=f"{self.ui_language['Close']['Runs']['Placeholder']}",
            style=TextStyle.short,
            required=True,
        )
        self.runscount = TextInput(
            label=f"{self.ui_language['Close']['RunsCount']['Label']}",
            placeholder=f"{self.ui_language['Close']['RunsCount']['Placeholder']}",
            default="1",
            style=TextStyle.short,
            required=True,
        )
        self.add_item(self.confirm)
        self.add_item(self.runs)
        self.add_item(self.runscount)

    async def on_submit(self, interaction: Interaction):

        if interaction is None:
            raise MissingInteractionError
        if interaction.guild is None:
            raise MissingGuildError

        confirm_val = self.confirm.value.strip().lower()
        runs_inc = self.runs.value.strip().lower()

        if confirm_val not in ["y", "n"] or runs_inc not in ["y", "n"]:
            error_msg = self.localization["Close"]["BadConfirmError"]
            await interaction.response.send_message(
                Utilities.format_error(self.user_language, error_msg)
            )
            return

        if confirm_val == "n":
            error_msg = self.localization["Close"]["CloseWithoutClose"]
            await interaction.response.send_message(
                Utilities.format_error(self.user_language, error_msg)
            )
            return

        # 2. Extract and validate run count early to avoid nesting the try/except
        inc_val = 0
        if runs_inc == "y":
            try:
                # Max 10 minimum 1.
                inc_val = max(1, min(int(self.runscount.value), 10))
            except ValueError:
                await interaction.response.send_message(
                    Utilities.format_error(
                        self.user_language, self.localization["Close"]["NotNumberError"]
                    )
                )
                return

            RosterExtended.increase_roster_count(
                self.bot.rosters[self.channel_id],
                inc_val,
                librarian=self.bot.librarian,
            )

        # 3. Handle Role Logic (Guards instead of Else)
        pingable_role = interaction.guild.get_role(
            self.bot.rosters[self.channel_id].pingable
        )
        if pingable_role is None:
            raise MissingRoleError

        await pingable_role.delete()

        # 4. Standard Deletion Sequence
        logging.info(f"Deleting Roster {self.name}")
        roster_data = self.bot.rosters[self.channel_id]
        delete_date = RosterExtended.create_undo_delete_date(
            roster_data.date, self.bot.config["raids"]["timezone"]
        )

        self.bot.librarian.put_undo_data(self.name, delete_date, roster_data)
        self.bot.librarian.delete_roster(self.channel_id)

        del self.bot.rosters[self.channel_id]
        logging.info("Roster Deleted")

        if self.channel:
            await self.channel.delete()

        # 5. Simplified response logic
        key = "Increase" if inc_val > 0 else "NoIncrease"
        msg = (
            self.localization["Close"][key] % (self.name, inc_val)
            if inc_val > 0
            else self.localization["Close"][key] % self.name
        )
        await interaction.response.send_message(msg)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
        )
        logging.error(f"Roster Close Error: {str(error)}")
