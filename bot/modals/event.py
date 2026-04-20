from discord.ui import Modal, TextInput
from discord import Interaction, TextStyle, Role
from discord.utils import get
from bot.services import Utilities, RosterExtended, EmbedFactory
import logging
import copy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class EventModal(Modal):
    def __init__(self, interaction: Interaction, bot, lang, channel_id=None):
        self.localization = bot.language[lang]["replies"]
        self.ui_localization = bot.language[lang]["ui"]
        self.user_language = lang
        self.bot = bot
        self.config = bot.config
        self.leader = None
        self.date_val = None
        self.memo_val = "None"
        self.new_roster = True
        self.new_name = f""
        self.channel_id = None
        self.change_name = True
        self.sort_channels = True
        self.event = f""
        self.event_roster = None
        self.channel = None
        if channel_id is not None:
            self.channel_id = channel_id
            self.old_roster = copy.copy(self.bot.rosters[self.channel_id])
            self.new_roster = False
            self.leader = f"{self.old_roster.leader}"
            self.event = f"{self.old_roster.event}"
            self.date_val = f"{self.old_roster.date}"
            self.memo_val = f"{self.old_roster.memo}"
            self.channel = interaction.guild.get_channel(int(self.channel_id))
        super().__init__(title=self.ui_localization["EventRoster"]["Title"])
        self.initialize()

    def initialize(self):
        # Add all the items here based on what is above
        self.leader_box = TextInput(
            label=self.ui_localization["EventRoster"]["Leader"]["Label"],
            placeholder=self.ui_localization["EventRoster"]["Leader"]["Placeholder"],
            default=self.leader,
            required=True,
        )
        self.event_box = TextInput(
            label=self.ui_localization["EventRoster"]["Event"]["Label"],
            placeholder=self.ui_localization["EventRoster"]["Event"]["Placeholder"],
            default=self.event,
            required=True,
        )
        self.date_box = TextInput(
            label=self.ui_localization["EventRoster"]["Date"]["Label"],
            placeholder=self.ui_localization["EventRoster"]["Date"]["Placeholder"],
            default=self.date_val,
            required=True,
        )
        self.memo_box = TextInput(
            label=self.ui_localization["EventRoster"]["Memo"]["Label"],
            default=self.memo_val,
            placeholder=self.ui_localization["EventRoster"]["Memo"]["Placeholder"],
            style=TextStyle.long,
            max_length=200,
            required=True,
        )
        self.add_item(self.leader_box)
        self.add_item(self.event_box)
        self.add_item(self.date_box)
        self.add_item(self.memo_box)

    async def on_submit(self, interaction: Interaction):
        try:
            leader = self.leader_box.value
            event = self.event_box.value
            memo = self.memo_box.value

            formatted_date = RosterExtended.format_date(self.date_box.value)
            category = interaction.guild.get_channel(self.config["raids"]["category"])

            if not self.new_roster:
                old_date = self.old_roster.date
                old_event = self.old_roster.event
                # Update all values then update the DB
                self.bot.rosters[self.channel_id].event = event
                self.bot.rosters[self.channel_id].leader = leader
                self.bot.rosters[self.channel_id].date = formatted_date
                self.bot.rosters[self.channel_id].memo = memo

                self.channel = interaction.guild.get_channel(int(self.channel_id))

                try:

                    day_change = RosterExtended.did_day_change(
                        old_date,
                        self.bot.rosters[self.channel_id].date,
                        self.config["raids"]["timezone"],
                    )
                    event_change = RosterExtended.did_trial_change(
                        old_event, self.bot.rosters[self.channel_id].event
                    )
                    if not day_change:
                        self.sort_channels = False

                    if not event_change:
                        self.change_name = False

                    if self.sort_channels or self.change_name:
                        new_name = RosterExtended.generate_channel_name(
                            formatted_date, event, self.config["raids"]["timezone"]
                        )
                        await self.channel.edit(name=new_name)

                    if day_change or event_change:
                        name = RosterExtended.create_pingable_role_name(
                            trial=event,
                            date=formatted_date,
                            tz=self.config["raids"]["timezone"],
                            guild=interaction.guild,
                        )
                        await interaction.guild.get_role(
                            self.bot.rosters[self.channel_id].pingable
                        ).edit(name=name)

                except ValueError as e:
                    await interaction.response.send_message(
                        f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['NewNameErr'])}"
                    )
                    logging.info(f"New Name Value Error Existing Roster: {e}")
                    return

            elif self.new_roster:
                try:
                    try:
                        logging.info(f"Creating new channel.")
                        new_name = RosterExtended.generate_channel_name(
                            formatted_date, event, self.config["raids"]["timezone"]
                        )
                        category = interaction.guild.get_channel(
                            self.config["raids"]["category"]
                        )
                        self.channel = await category.create_text_channel(new_name)
                        logging.info(
                            f"Roster Channel: channelID: {str(self.channel.id)}"
                        )
                        self.channel_id = (
                            self.channel.id
                        )  # Set new rosters channel to the id.
                    except Exception as e:
                        await interaction.response.send_message(
                            f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['CantCreate'])}"
                        )
                        logging.error(f"Unable To Create New Roster Channel: {str(e)}")
                        return
                    group_role = RosterExtended.create_pingable_role_name(
                        trial=event,
                        date=formatted_date,
                        tz=self.config["raids"]["timezone"],
                        guild=interaction.guild,
                    )
                    role: Role = await interaction.guild.create_role(
                        name=group_role, mentionable=True
                    )
                    self.bot.rosters[self.channel_id] = RosterExtended.event_factory(
                        leader, event, formatted_date, memo, role.id
                    )

                    embed = EmbedFactory.create_new_event_roster(
                        event=self.bot.rosters[self.channel_id].event,
                        date=self.bot.rosters[self.channel_id].date,
                        leader=self.bot.rosters[self.channel_id].leader,
                        memo=self.bot.rosters[self.channel_id].memo,
                        pingable=self.bot.rosters[self.channel_id].pingable,
                    )
                    await self.channel.send(embed=embed)
                except Exception as e:
                    await interaction.response.send_message(
                        f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['CantEmbed'])}"
                    )
                    logging.error(
                        f"Event Roster Creation Channel And Embed Error: {str(e)}"
                    )
                    return
            else:
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.localization['Unreachable'])}"
                )
                return
        except Exception as e:
            logging.error(
                f"Event Roster Error During Channel Create and Embed: {str(e)}"
            )
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['Unreachable'])}"
            )
            return

        self.bot.librarian.put_roster(
            self.channel_id, self.bot.rosters[self.channel_id]
        )
        if self.new_roster:
            await interaction.response.send_message(
                f"{self.bot.language[self.user_language]['replies']['EventModify']['NewRosterCreated'] % self.channel.name}"
            )

        elif not self.new_roster:
            await interaction.response.send_message(
                f"{self.bot.language[self.user_language]['replies']['EventModify']['ExistingUpdated'] % self.channel.name}"
            )
        return

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
        )
        logging.error(f"Trial Creation/Modify Error: {str(error)}")
        return
