from discord import ui, SelectOption, Interaction
from bot.services import Utilities
from bot.modals import *
from bot.models import Roster, EventRoster


class RosterSelect(ui.Select):
    def __init__(self, interaction: Interaction, cmd_called, bot, user_language):
        self.channels = {}
        self.config = bot.config
        self.cmd_called = cmd_called
        self.language = bot.language[user_language]["replies"]
        self.ui_language = bot.language[user_language]["ui"]
        self.user_language = user_language
        self.bot = bot
        self.rosters = bot.rosters
        self.channel_mapper = {}
        self.limits = bot.limits

        options = []
        if self.rosters is None or len(self.rosters) == 0:
            options.append(SelectOption(label="N/A", value="N/A"))
        else:
            used = []
            for i in self.rosters:
                channel = self.bot.get_channel(int(i))
                label = channel.name if channel else f"{i}"
                if label in used:
                    found = True
                    count = 1
                    while found:
                        new_label = f"{label}{count}".strip()
                        if new_label not in used:
                            label = new_label
                            self.channel_mapper[label] = i
                            break
                        count += 1
                options.append(SelectOption(label=label, value=str(i)))
                self.channel_mapper[label] = i
                used.append(label)

        # discord.SelectOption(label="Option 1",emoji="👌",description="This is option 1!"),
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

        # Fetch channel ID directly from option value
        channel_id = int(selected)

        roster = self.rosters[channel_id]

        if self.cmd_called == "modify":
            if isinstance(self.bot.rosters[channel_id], Roster):
                await interaction.response.send_modal(
                    TrialModal(
                        interaction=interaction,
                        bot=self.bot,
                        lang=self.user_language,
                        channel_id=channel_id,
                    )
                )
            elif isinstance(self.bot.rosters[channel_id], EventRoster):
                await interaction.response.send_modal(
                    EventModal(
                        interaction=interaction,
                        bot=self.bot,
                        lang=self.user_language,
                        channel_id=channel_id,
                    )
                )
        elif self.cmd_called == "close":
            await interaction.response.send_modal(
                CloseModal(
                    interaction=interaction,
                    bot=self.bot,
                    lang=self.user_language,
                    channel_id=channel_id,
                )
            )
        elif self.cmd_called == "remove":
            await interaction.response.send_modal(
                RemoveModal(
                    interaction=interaction,
                    bot=self.bot,
                    user_lang=self.user_language,
                    channel_id=channel_id,
                )
            )
        elif self.cmd_called == "run_count":
            await interaction.response.send_modal(
                RunCountModal(
                    interaction=interaction,
                    bot=self.bot,
                    users_language=self.user_language,
                    channel_id=channel_id,
                )
            )
        elif self.cmd_called == "fill":
            await interaction.response.send_modal(
                FillModal(
                    interaction=interaction,
                    bot=self.bot,
                    user_language=self.user_language,
                    channel_id=channel_id,
                )
            )


class RosterSelector(ui.View):
    def __init__(
        self,
        interaction: Interaction,
        bot,
        caller,
        cmd_called,
        user_language,
        *,
        timeout=30,
    ):
        super().__init__(timeout=timeout)
        self.caller = caller
        self.bot = bot
        self.interaction = interaction
        self.language = bot.language[user_language]
        self.user_language = user_language
        self.new_roster_select = RosterSelect(
            interaction, cmd_called, bot, user_language
        )
        self.add_item(self.new_roster_select)

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.caller.id:
            await interaction.response.send_message(
                f"{self.language['SelectRoster']['NotCaller']}", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self.new_roster_select.update_options_timeout()
        self.clear_items()
        self.stop()
