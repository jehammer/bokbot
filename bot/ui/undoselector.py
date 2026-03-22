from discord import ui, SelectOption, Interaction
from bot.services import Utilities
from bot.modals import *
from bot.models import Roster, EventRoster


class UndoSelect(ui.Select):
    def __init__(self, interaction: Interaction, bot, user_language):
        self.config = bot.config
        self.language = bot.language[user_language]["replies"]
        self.ui_language = bot.language[user_language]["ui"]
        self.user_language = user_language
        self.bot = bot
        self.mapper = {}

        options = []
        data = self.bot.librarian.get_undo_data()
        self.rosters = data
        if data is None or len(data) == 0:
            options.append(SelectOption(label="N/A"))
        else:
            used = []
            for i in data:
                label = i
                if label in used:
                    found = True
                    count = 1
                    while found:
                        new_label = f"{label}{count}".strip()
                        if new_label not in used:
                            label = new_label
                            self.mapper[label] = i
                            break
                        count += 1
                options.append(SelectOption(label=label))
                self.mapper[label] = i
                used.append(label)

        super().__init__(
            placeholder=self.ui_language["SelectRoster"]["Placeholder"],
            max_values=1,
            min_values=1,
            options=options,
        )

    def update_options_timeout(self):
        # Remove all options and set the placeholder to "Timed out"
        self.options = []
        self.placeholder = "Timed out"

    async def callback(self, interaction: Interaction):
        selected = self.values[0]

        if selected == "N/A":
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.language['SelectRoster']['NoOptionsError'])}"
            )
            return

        channel_name = self.mapper[selected]

        await interaction.response.send_modal(
            UndoModal(
                interaction=interaction,
                bot=self.bot,
                users_language=self.user_language,
                roster=self.rosters[channel_name],
                roster_name=channel_name,
            )
        )


class UndoSelector(ui.View):
    def __init__(
        self, interaction: Interaction, bot, caller, user_language, *, timeout=30
    ):
        super().__init__(timeout=timeout)
        self.caller = caller
        self.bot = bot
        self.interaction = interaction
        self.language = bot.language[user_language]
        self.user_language = user_language
        self.new_undo_select = UndoSelect(interaction, bot, user_language)
        self.add_item(self.new_undo_select)

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.caller.id:
            await interaction.response.send_message(
                f"{self.language['SelectRoster']['NotCaller']}", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self.new_undo_select.update_options_timeout()
        self.clear_items()
        self.stop()
