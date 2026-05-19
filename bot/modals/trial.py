from bot.models.roster import Roster
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


class TrialModal(Modal):
    def __init__(self, interaction: Interaction, bot, lang, channel_id=None):
        self.localization = bot.language[lang]["replies"]
        self.ui_localization = bot.language[lang]["ui"]
        self.config = bot.config
        self.limits = bot.limits
        self.leader_trial_val = None
        self.date_val = None
        self.limit_val = None
        self.role_nums_val = "8,2,2"
        self.memo_val = "None"
        self.new_roster = True
        self.new_name = f""
        self.user_language = lang
        self.bot = bot
        self.channel = None
        self.change_name = True
        self.sort_channels = True
        self.channel_id = channel_id
        if self.channel_id is not None:
            self.channel_id = channel_id
            self.new_roster = False
            self.old_roster = copy.deepcopy(self.bot.rosters[self.channel_id])
            self.leader_trial_val = f"{self.old_roster.leader},{self.old_roster.trial}"
            self.date_val = f"{self.old_roster.date}"
            self.limit_val = f"{self.old_roster.role_limit}"
            self.role_nums_val = f"{self.old_roster.dps_limit},{self.old_roster.healer_limit},{self.old_roster.tank_limit}"
            self.memo_val = f"{self.old_roster.memo}"
        super().__init__(title=self.ui_localization["TrialModify"]["Title"])
        self.initialize()

    def initialize(self):
        # Add all the items here based on what is above
        self.leader_trial = TextInput(
            label=self.ui_localization["TrialModify"]["LeaderTrial"]["Label"],
            placeholder=self.ui_localization["TrialModify"]["LeaderTrial"][
                "Placeholder"
            ],
            default=self.leader_trial_val,
            required=True,
        )
        self.date = TextInput(
            label=self.ui_localization["TrialModify"]["Date"]["Label"],
            placeholder=self.ui_localization["TrialModify"]["Date"]["Placeholder"],
            default=self.date_val,
            required=True,
        )
        self.limit = TextInput(
            label=self.ui_localization["TrialModify"]["Limit"]["Label"],
            placeholder=self.ui_localization["TrialModify"]["Limit"]["Placeholder"],
            default=self.limit_val,
            required=True,
        )
        self.role_nums = TextInput(
            label=self.ui_localization["TrialModify"]["RoleNums"]["Label"],
            default=self.role_nums_val,
            required=True,
        )
        self.memo = TextInput(
            label=self.ui_localization["TrialModify"]["Memo"]["Label"],
            default=self.memo_val,
            placeholder=self.ui_localization["TrialModify"]["Memo"]["Placeholder"],
            style=TextStyle.long,
            max_length=600,
            required=True,
        )
        self.add_item(self.leader_trial)
        self.add_item(self.date)
        self.add_item(self.limit)
        self.add_item(self.role_nums)
        self.add_item(self.memo)

    async def on_submit(self, interaction: Interaction):
        # Split the values:
        try:
            roles = self.limits

            role_limit = int(self.limit.value)
            if role_limit < 0 or role_limit > len(roles):
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadLimit'] % len(roles))}"
                )
                return
        except (NameError, ValueError) as e:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidLimit'] % self.limit.value)}"
            )
            return
        try:
            leader, trial = self.leader_trial.value.split(",")
            trial.lstrip()
        except (NameError, ValueError):
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadLeaderTrial'] % self.leader_trial.value)}"
            )
            return
        try:
            dps_limit, healer_limit, tank_limit = self.role_nums.value.split(",")
        except (NameError, ValueError):
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadRoleNums'] % self.role_nums.value)}"
            )
            return
        try:
            dps_limit = int(dps_limit.strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidDPS'] % dps_limit)}"
            )
            return
        try:
            healer_limit = int(healer_limit.strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidHealers'] % healer_limit)}`"
            )
            return
        try:
            tank_limit = int(tank_limit.strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidTanks'] % tank_limit)}"
            )
            return

        try:
            formatted_date = RosterExtended.format_date(self.date.value)
            category = interaction.guild.get_channel(self.config["raids"]["category"])

            if not self.new_roster:
                # Update all values then update the DB
                self.bot.rosters[self.channel_id].trial = trial
                self.bot.rosters[self.channel_id].leader = leader
                self.bot.rosters[self.channel_id].dps_limit = dps_limit
                self.bot.rosters[self.channel_id].healer_limit = healer_limit
                self.bot.rosters[self.channel_id].tank_limit = tank_limit
                self.bot.rosters[self.channel_id].date = formatted_date
                self.bot.rosters[self.channel_id].memo = self.memo.value
                self.bot.rosters[self.channel_id].role_limit = role_limit

                self.channel = interaction.guild.get_channel(int(self.channel_id))

                # Account for role changes where there is overflow
                self.bot.rosters[self.channel_id].push_excess_to_overflow()

                try:

                    day_change = RosterExtended.did_day_change(
                        self.old_roster.date,
                        self.bot.rosters[self.channel_id].date,
                        self.config["raids"]["timezone"],
                    )
                    trial_change = RosterExtended.did_trial_change(
                        self.old_roster.trial, self.bot.rosters[self.channel_id].trial
                    )
                    if not day_change:
                        self.sort_channels = False

                    if not trial_change:
                        self.change_name = False

                    if self.sort_channels or self.change_name:
                        self.new_name = RosterExtended.generate_channel_name(
                            formatted_date, trial, self.config["raids"]["timezone"]
                        )
                        await self.channel.edit(name=self.new_name)

                    if day_change or trial_change:
                        name = RosterExtended.create_pingable_role_name(
                            trial=self.bot.rosters[self.channel_id].trial,
                            date=self.bot.rosters[self.channel_id].date,
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
                    logging.info(f"Creating new channel.")
                    try:
                        new_name = RosterExtended.generate_channel_name(
                            formatted_date, trial, self.config["raids"]["timezone"]
                        )
                        self.channel = await category.create_text_channel(new_name)
                        self.channel_id = self.channel.id
                    except Exception as e:
                        await interaction.response.send_message(
                            f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['CantCreate'])}"
                        )
                        logging.error(f"Unable To Create New Roster Channel: {str(e)}")
                        return

                    self.bot.rosters[self.channel_id] = RosterExtended.factory(
                        leader,
                        trial,
                        formatted_date,
                        dps_limit,
                        healer_limit,
                        tank_limit,
                        role_limit,
                        self.memo.value,
                        self.config,
                    )

                    group_role = RosterExtended.create_pingable_role_name(
                        trial=self.bot.rosters[self.channel_id].trial,
                        date=self.bot.rosters[self.channel_id].date,
                        tz=self.config["raids"]["timezone"],
                        guild=interaction.guild,
                    )

                    role: Role = await interaction.guild.create_role(
                        name=group_role, mentionable=True
                    )
                    self.bot.rosters[self.channel_id].pingable = role.id
                    roles_req = ""
                    if isinstance(roles[role_limit], list):
                        # Need to work with 3 roles to check, dps | tank | healer order

                        limiter_dps = get(
                            interaction.guild.roles, name=roles[role_limit][0]
                        )
                        limiter_tank = get(
                            interaction.guild.roles, name=roles[role_limit][1]
                        )
                        limiter_healer = get(
                            interaction.guild.roles, name=roles[role_limit][2]
                        )

                        roles_req += f"{limiter_dps.mention} {limiter_tank.mention} {limiter_healer.mention}"

                    else:
                        limiter = get(interaction.guild.roles, name=roles[role_limit])
                        roles_req += f"{limiter.mention}"

                    embed = EmbedFactory.create_new_roster(
                        trial=self.bot.rosters[self.channel_id].trial,
                        date=self.bot.rosters[self.channel_id].date,
                        roles_req=roles_req,
                        leader=self.bot.rosters[self.channel_id].leader,
                        memo=self.bot.rosters[self.channel_id].memo,
                        pingable=self.bot.rosters[self.channel_id].pingable,
                    )
                    await self.channel.send(embed=embed)

                    logging.info(f"Roster Channel: channelID: {str(self.channel.id)}")
                    self.channel_id = self.channel.id

                except Exception as e:
                    await interaction.response.send_message(
                        f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['CantEmbed'])}"
                    )
                    logging.error(f"Raid Creation Channel And Embed Error: {str(e)}")
                    return
            else:
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.localization['Unreachable'])}"
                )
                return
        except Exception as e:
            logging.error(
                f"Trial/Modify Error During Channel Create and Embed: {str(e)}"
            )
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['Unreachable'])}"
            )
            return

        self.bot.librarian.put_roster(
            self.channel_id, self.bot.rosters[self.channel_id]
        )
        self.bot.dispatch("sort_rosters")

        if self.new_roster:
            await interaction.response.send_message(
                f"{self.bot.language[self.user_language]['replies']['TrialModify']['NewRosterCreated'] % self.channel.name}"
            )

        elif not self.new_roster:
            await interaction.response.send_message(
                f"{self.bot.language[self.user_language]['replies']['TrialModify']['ExistingUpdated'] % self.channel.name}"
            )

        return

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
        )
        logging.error(f"Trial Creation/Modify Error: {str(error)}")
        return
