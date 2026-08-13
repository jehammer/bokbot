import calendar

from discord import Embed, Color, Member
import logging
from bot.models import Roster, Rank, Count, EventRoster
from bot.services.utilities import Utilities

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[logging.FileHandler("log.log", mode="a"), logging.StreamHandler()],
)  # , datefmt="%Y-%m-%d %H:%M:%S")


class EmbedFactory:
    """Class of Static Methods that create and return embeds"""

    @staticmethod
    def create_status(roster: Roster, language, bot, roles_req, guild):
        try:

            desc = f"{language.get('Rank')} {roles_req}\n{language.get('Pingable')} <@&{roster.pingable}>"
            if roster.memo != "None":
                desc += f"\n\n{roster.memo}"

            embed = Embed(
                title=f"{roster.trial.replace('_', r'\_')} {roster.date}",
                description=desc,
                color=Color.green(),
            )
            embed.set_footer(text=language.get("Footer"))
            embed.set_author(
                name=f"{language.get('Author')} {roster.leader.replace('_', r'_')}"
            )

            # Helper to build a field for a given bucket
            def build_field(field_bucket, emoji_key):
                field_names = ""
                count = 0
                for user_id, msg in field_bucket.items():
                    member = guild.get_member(int(user_id))
                    if member:
                        field_names += f"{bot.config['raids'][emoji_key]}{member.display_name.replace('_', r'\_')}\n"
                        if msg:
                            field_names += f"{msg.replace('_', r'\_')}\n"
                        count += 1
                return field_names, count

            display_order = ["tank", "healer", "dps"]

            # Main
            for role in display_order:
                main, _, _ = roster.role_map[role]
                limit = getattr(roster, f"{role}_limit")
                role_label = "DPS" if role == "dps" else role.capitalize()

                bucket = getattr(roster, main)
                names, main_count = build_field(bucket, f"{role}_emoji")
                embed.add_field(
                    name=(
                        f"{language.get(role_label+'s')} {main_count}/{limit}"
                        if role != "dps"
                        else f"{language.get(role_label)} {main_count}/{limit}"
                    ),
                    value=names if names else "\u200b",
                    inline=True,
                )
            # Overflow
            for role in display_order:
                _, _, overflow = roster.role_map[role]
                role_label = "DPS" if role == "dps" else role.capitalize() + "s"
                # Overflow bucket
                bucket = getattr(roster, overflow)
                names, overflow_count = build_field(bucket, f"{role}_emoji")
                if overflow_count > 0:
                    embed.add_field(
                        name=language.get(f"Overflow_{role_label}"),
                        value=names,
                        inline=True,
                    )

            # Backup
            for role in display_order:
                _, backup, _ = roster.role_map[role]
                role_label = "DPS" if role == "dps" else role.capitalize() + "s"
                bucket = getattr(roster, backup)
                names, backup_count = build_field(bucket, f"{role}_emoji")
                if backup_count > 0:
                    embed.add_field(
                        name=language.get(f"Backup_{role_label}"),
                        value=names,
                        inline=True,
                    )

            return embed

        except Exception as e:
            logging.error(f"Status Embed Create Error: {e}")
            raise e

    @staticmethod
    def create_new_roster(trial, date, roles_req, leader, memo, pingable):
        # Unlike with other commands, creating a new Roster is always in english

        # Generate the description
        desc = f"Rank(s) Required: {roles_req}\nGroup: <@&{pingable}>"

        if memo != "None":
            desc += f"\n\n{memo}"

        desc += f"\n\nI hope people sign up for this."

        embed = Embed(title=f"{trial} {date}", description=desc, color=Color.blue())
        embed.set_footer(
            text="Remember to spay or neuter your support!\nAnd mention your sets!"
        )
        embed.set_author(name="Raid Lead: " + leader)
        embed.add_field(name="Calling Healers!", value="To Heal Us!", inline=False)
        embed.add_field(name="Calling Tanks!", value="To Be Stronk!", inline=False)
        embed.add_field(name="Calling DPS!", value="To Stand In Stupid!", inline=False)

        return embed

    @staticmethod
    def create_ranking(rank: Rank, lang, name):
        embed = Embed(title=name, color=Color.red())
        embed.set_footer(text=f"{lang['Footer']}")
        embed.set_author(name=f"{lang['Author']}")
        embed.add_field(name=f"{lang['Total'] % rank.count}", value=" ", inline=False)
        embed.add_field(
            name=f"{lang['Last'] % rank.last_called}", value=" ", inline=False
        )
        embed.add_field(name=f"{lang['Lowest'] % rank.lowest}", value=" ", inline=False)
        embed.add_field(
            name=f"{lang['Highest'] % rank.highest}", value=" ", inline=False
        )
        embed.add_field(
            name=f"{lang['Singles'] % rank.singles}", value=" ", inline=False
        )
        embed.add_field(
            name=f"{lang['Doubles'] % rank.doubles}", value=" ", inline=False
        )
        embed.add_field(
            name=f"{lang['Samsies'] % rank.samsies}", value=" ", inline=False
        )
        embed.add_field(
            name=f"{lang['SixNine'] % rank.six_nine}", value=" ", inline=False
        )
        embed.add_field(
            name=f"{lang['FourTwenty'] % rank.four_twenty}", value=" ", inline=False
        )
        embed.add_field(name=f"{lang['Boob'] % rank.boob}", value=" ", inline=False)
        embed.add_field(name=f"{lang['Pie'] % rank.pie}", value=" ", inline=False)
        embed.add_field(
            name=f"{lang['Palindrome'] % rank.palindrome}", value=" ", inline=False
        )
        return embed

    @staticmethod
    def create_count(count: Count, lang, name, guild_name):
        embed = Embed(title=name, color=Color.orange())
        embed.set_footer(text=f"{lang['Footer']}")
        embed.set_author(name=f"{lang['Author'] % guild_name}")
        embed.add_field(name=f"{lang['Total']}", value=count.count, inline=True)
        embed.add_field(name=f"{lang['LastRan']}", value=count.lastTrial, inline=True)
        embed.add_field(name=f"{lang['LastDate']}", value=count.lastDate, inline=True)
        embed.add_field(
            name=f"{lang['Stats']}", value=f"{lang['RoleRuns']}", inline=False
        )
        embed.add_field(name=f"{lang['DPS']}", value=count.dpsRuns, inline=True)
        embed.add_field(name=f"{lang['Tank']}", value=count.tankRuns, inline=True)
        embed.add_field(name=f"{lang['Healer']}", value=count.healerRuns, inline=True)
        embed.add_field(
            name=f"{lang['Other']}", value=f"{lang['OtherRuns']}", inline=False
        )
        embed.add_field(name=f"{lang['Event']}", value=count.eventRuns, inline=True)
        return embed

    @staticmethod
    def create_new_event_roster(pingable, memo, leader, event, date):
        desc = f"Group: <@&{pingable}>"

        if memo != "None":
            desc += f"\n\n{memo}"

        desc += f"\n\nI hope people sign up for this."

        embed = Embed(title=f"{event} {date}", description=desc, color=Color.blue())
        embed.set_footer(text="Remember to spay or neuter your mounts!")
        embed.set_author(name="Leader: " + leader)
        embed.add_field(
            name="Calling Guildies!", value="To Come Do The Thing!", inline=False
        )

        return embed

    @staticmethod
    def create_event_roster(roster: EventRoster, language, bot, guild):
        try:
            count = 0

            desc = f"{language['Pingable']} <@&{roster.pingable}>"

            if roster.memo != "None":
                desc += f"\n\n{roster.memo}"

            embed = Embed(
                title=f"{roster.event.replace('_', r'\_')} {roster.date}",
                description=desc,
                color=Color.green(),
            )
            embed.set_footer(text=f"{language['Footer']}")
            embed.set_author(
                name=f"{language['Author']} {roster.leader.replace("_", r"\_")}"
            )

            count = 0
            group_count = 1
            names = ""
            if not len(roster.members) == 0:
                for i in roster.members:
                    if count == 12:
                        embed.add_field(
                            name=f"{language['Members']} {group_count}",
                            value=names,
                            inline=True,
                        )
                        names = ""
                        count = 0
                        group_count += 1
                    member_name = guild.get_member(int(i))
                    if member_name is not None:
                        names += f"{bot.config['raids']['event_emoji']}{member_name.display_name.replace("_", r"\_")}\n"
                        if roster.members[i] != "":
                            names += f"{roster.members[i].replace("_", r"\_")}\n"
                        count += 1

            embed.add_field(
                name=f"{language['Members']} {group_count}", value=names, inline=True
            )

            return embed
        except Exception as e:
            logging.error(f"Status Embed Create Error: {e}")
            raise e

    @staticmethod
    def create_member_leave_embed(
        count: Count | None,
        rank: Rank | None,
        member: Member,
        rosters_removed,
        lang,
    ):
        assert member.joined_at is not None
        embed = Embed(
            title=f"{member.name} - {member.display_name}",
            description=f"Joined:  {calendar.month_name[member.joined_at.month]} {member.joined_at.day}{Utilities.suffix(member.joined_at.day)} {member.joined_at.year}",
        )
        embed.set_author(name="TRAITOR ALERT")
        embed.add_field(
            name="Active Rosters Removed",
            value=", ".join(rosters_removed) if rosters_removed else "None",
            inline=False,
        )

        last_ran_data = (
            f"{count.lastTrial} on {count.lastDate}\nDPS: {count.dpsRuns} | Tank: {count.tankRuns} | Healer: {count.healerRuns} | Event: {count.eventRuns}"
            if count and count.lastTrial and count.lastDate
            else "N/A"
        )

        last_ranking_data = (
            f"Total: {rank.count}\nLast: {rank.last_called}\nLowest: {rank.lowest}\nHighest: {rank.highest}\nSingles: {rank.singles}\nDoubles: {rank.doubles}\nSamsies: {rank.samsies}\n69s: {rank.six_nine}\n420s: {rank.four_twenty}\nBoobs: {rank.boob}\nPies: {rank.pie}\nPalindromes: {rank.palindrome}"
            if rank and rank.count > 0
            else "N/A"
        )

        embed.add_field(name="Last Ran", value=last_ran_data, inline=False)
        embed.add_field(name="Last Ranking", value=last_ranking_data, inline=False)
        return embed
