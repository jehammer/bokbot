from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput
from bot.models import Roster
from bot.models.bokbot import BOKBot
from bot.services import Utilities, RosterExtended
from bot.database import Librarian
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class CloseModal(Modal):
    def __init__(self, interaction: Interaction, bot: BOKBot, lang, channel_id):
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
        confirm_value = self.confirm.value.strip().lower()
        runs_inc = self.runs.value.strip().lower()
        if (
            confirm_value != "n"
            and confirm_value != "y"
            and runs_inc != "n"
            and runs_inc != "y"
        ):
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['Close']['BadConfirmError'])}"
            )
            return
        if confirm_value != "y":
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['Close']['CloseWithoutClose'])}"
            )
            return
        runs_increased = False
        inc_val = 0
        if runs_inc == "y":
            try:
                inc_val = int(self.runscount.value)
                if inc_val < 1:
                    inc_val = 1
                elif inc_val > 10:
                    raise ValueError
                RosterExtended.increase_roster_count(
                    self.bot.rosters[self.channel_id],
                    inc_val,
                    librarian=self.bot.librarian,
                )
                runs_increased = True
            except ValueError:
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.localization['Close']['NotNumberError'])}"
                )
                return

        logging.info(f"Deleting Roster {self.name}")
        delete_date = RosterExtended.create_undo_delete_date(
            self.bot.rosters[self.channel_id].date, self.bot.config["raids"]["timezone"]
        )
        self.bot.librarian.put_undo_data(
            channel_name=self.name,
            delete_date=delete_date,
            data=self.bot.rosters[self.channel_id],
        )
        await interaction.guild.get_role(
            self.bot.rosters[self.channel_id].pingable
        ).delete()
        self.bot.librarian.delete_roster(self.channel_id)
        del self.bot.rosters[self.channel_id]
        logging.info(f"Roster Deleted")

        if self.channel is not None:
            await self.channel.delete()
        if runs_increased:
            await interaction.response.send_message(
                f"{self.localization['Close']['Increase'] % (self.name, inc_val)}"
            )
        else:
            await interaction.response.send_message(
                f"{self.localization['Close']['NoIncrease'] % self.name}"
            )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
        )
        logging.error(f"Roster Close Error: {str(error)}")
