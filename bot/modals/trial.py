from bot.models import Roster
from discord.ui import Modal, TextInput
from discord import Interaction, TextStyle
from discord.utils import get
from bot.services import Utilities, RosterExtended, EmbedFactory
import logging
import copy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)


class TrialModal(Modal):
    def __init__(self, interaction: Interaction, bot, lang, channel_id=None):
        self.new_roster = True
        self.old_roster: Roster | None = (
            copy.deepcopy(bot.rosters[channel_id]) if channel_id else None
        )
        self.new_roster = False if self.old_roster else True
        self.leader_trial_val = (
            f"{self.old_roster.leader},{self.old_roster.trial}"
            if self.old_roster
            else ""
        )
        self.date_val = f"{self.old_roster.date}" if self.old_roster else ""
        self.limit_val = f"{self.old_roster.role_limit}" if self.old_roster else ""
        self.role_nums_val = (
            f"{self.old_roster.dps_limit},{self.old_roster.healer_limit},{self.old_roster.tank_limit}"
            if self.old_roster
            else "8,2,2"
        )
        self.memo_val = f"{self.old_roster.memo}" if self.old_roster else "None"
        self.new_name = ""
        self.localization = bot.language[lang]["replies"]
        self.ui_localization = bot.language[lang]["ui"]
        self.config = bot.config
        self.limits = bot.limits
        self.user_language = lang
        self.bot = bot
        self.channel = None
        self.change_name = True
        self.sort_channels = True
        self.channel_id = channel_id if channel_id else ""
        super().__init__(title=self.ui_localization["TrialModify"]["Title"])
        self.initialize()

    def initialize(self):
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

    async def validator(self, interaction: Interaction):
        """Validation of user inputs for a new roster"""
        curr_val = ""
        # Role Limit
        curr_val = self.limit.value
        role_limit = int(curr_val)
        if role_limit < 0 or role_limit > len(self.limits):
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadLimit'] % len(self.limits))}"
            )
            return None

        # Leader/Trial
        curr_val = self.leader_trial.value
        if "," not in curr_val:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadLeaderTrial'] % curr_val)}"
            )
            return None
        leader, trial = [x.strip() for x in curr_val.split(",")]

        # Role Nums Split
        curr_val = self.role_nums.value
        if self.role_nums.value.count(",") != 2:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['BadRoleNums'] % curr_val)}"
            )
            return None

        # Role Nums DPS then Heal and Tank
        raw_nums = self.role_nums.value.split(",")
        try:
            dps = int(raw_nums[0].strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidDPS'] % raw_nums[0])}"
            )
            return None

        try:
            heal = int(raw_nums[1].strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidHealers'] % raw_nums[1])}"
            )
            return None

        try:
            tank = int(raw_nums[2].strip())
        except ValueError:
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['TrialModify']['InvalidTanks'] % raw_nums[2])}"
            )
            return None

        return {
            "role_limit": role_limit,
            "leader": leader,
            "trial": trial,
            "dps": dps,
            "healer": heal,
            "tank": tank,
            "date": RosterExtended.format_date(self.date.value),
        }

    async def update_existing_roster(self, interaction: Interaction, data):
        """Update Existing Rosters with new data"""
        if self.old_roster is None:
            raise RuntimeError("Old roster is missing. Blame Arma or Lily")
        roster = self.bot.rosters[self.channel_id]
        roster.trial, roster.leader = data["trial"], data["leader"]
        roster.dps_limit, roster.healer_limit, roster.tank_limit = (
            data["dps"],
            data["healer"],
            data["tank"],
        )
        roster.date, roster.memo, roster.role_limit = (
            data["date"],
            self.memo.value,
            data["role_limit"],
        )

        if interaction.guild is None:
            raise RuntimeError(
                f"{Utilities.format_error(self.user_language, self.localization['MissingGuild'])}"
            )

        self.channel = interaction.guild.get_channel(int(self.channel_id))
        if self.channel is None:
            raise ValueError("Channel not found. Blame Arma or Lily")
        roster.push_excess_to_overflow()

        day_change = RosterExtended.did_day_change(
            self.old_roster.date, data["date"], self.config["raids"]["timezone"]
        )
        trial_change = RosterExtended.did_trial_change(
            self.old_roster.trial, data["trial"]
        )

        if not day_change:
            self.sort_channels = False
        if not trial_change:
            self.change_name = False

        if self.sort_channels or self.change_name:
            self.new_name = RosterExtended.generate_channel_name(
                data["date"], data["trial"], self.config["raids"]["timezone"]
            )
            await self.channel.edit(name=self.new_name)

        if day_change or trial_change:
            name = RosterExtended.create_pingable_role_name(
                trial=roster.trial,
                date=roster.date,
                tz=self.config["raids"]["timezone"],
                guild=interaction.guild,
            )
            if role := interaction.guild.get_role(roster.pingable):
                await role.edit(name=name)
            else:
                raise ValueError("Role not found. Blame Arma or Lily")

    async def create_new_roster(self, interaction: Interaction, data, category):
        """Create a new roster with input data"""

        if interaction.guild is None:
            raise RuntimeError(
                f"{Utilities.format_error(self.user_language, self.localization['MissingGuild'])}"
            )
        new_name = RosterExtended.generate_channel_name(
            data["date"], data["trial"], self.config["raids"]["timezone"]
        )
        self.channel = await category.create_text_channel(new_name)
        if self.channel is None:
            raise ValueError("Channel not found. Blame Arma or Lily")
        self.channel_id = self.channel.id

        self.bot.rosters[self.channel_id] = RosterExtended.factory(
            data["leader"],
            data["trial"],
            data["date"],
            data["dps"],
            data["healer"],
            data["tank"],
            data["role_limit"],
            self.memo.value,
            self.config,
        )

        group_role_name = RosterExtended.create_pingable_role_name(
            trial=data["trial"],
            date=data["date"],
            tz=self.config["raids"]["timezone"],
            guild=interaction.guild,
        )
        group_role = await interaction.guild.create_role(
            name=group_role_name, mentionable=True
        )
        self.bot.rosters[self.channel_id].pingable = group_role.id

        # Determine mentions
        roles_req = ""
        current_limit = self.limits[data["role_limit"]]
        if isinstance(current_limit, list):
            mentions = [
                role.mention
                for n in current_limit
                if (role := get(interaction.guild.roles, name=n)) is not None
            ]
            roles_req = " ".join(mentions)
        else:
            role = get(interaction.guild.roles, name=current_limit)
            if role is not None:
                roles_req = role.mention

        embed = EmbedFactory.create_new_roster(
            trial=data["trial"],
            date=data["date"],
            roles_req=roles_req,
            leader=data["leader"],
            memo=self.memo.value,
            pingable=group_role.id,
        )
        await self.channel.send(embed=embed)

    async def on_submit(self, interaction: Interaction):
        if interaction is None:
            raise ValueError("Interaction is missing. Blame Arma or Lily")
        if interaction.guild is None:
            raise ValueError(
                f"{Utilities.format_error(self.user_language, self.localization['MissingGuild'])}"
            )
        data = await self.validator(interaction)
        if not data:
            return

        try:
            category = interaction.guild.get_channel(self.config["raids"]["category"])
            if category is None:
                raise ValueError("Category not found. Blame Arma or Lily")
            if self.new_roster:
                await self.create_new_roster(interaction, data, category)
            else:
                await self.update_existing_roster(interaction, data)

            if self.channel is None:
                raise ValueError("Channel is missing.")

            self.bot.librarian.put_roster(
                self.channel_id, self.bot.rosters[self.channel_id]
            )
            self.bot.dispatch("sort_rosters")

            res_key = "NewRosterCreated" if self.new_roster else "ExistingUpdated"
            await interaction.response.send_message(
                f"{self.localization['TrialModify'][res_key] % self.channel.name}"
            )

        except Exception as e:
            logging.error(f"Submit Error: {str(e)}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
                )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"{Utilities.format_error(self.user_language, self.localization['Incomplete'])}"
            )
        logging.error(f"Trial Modal Global Error: {str(error)}")
