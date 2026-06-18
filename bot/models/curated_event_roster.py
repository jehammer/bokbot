import logging


class CuratedEventRoster:
    """Class for handling roster and related information for curated events that require support spots to be set."""

    def __init__(
        self,
        event,
        date,
        leader,
        dps=None,
        healers=None,
        tanks=None,
        dps_limit=0,
        healer_limit=0,
        tank_limit=0,
        memo="delete",
        pingable="None",
    ):
        self.event = event
        self.date = date
        self.leader = leader

        self.dps = dps or {}
        self.healers = healers or {}
        self.tanks = tanks or {}

        self.dps_limit = dps_limit
        self.healer_limit = healer_limit
        self.tank_limit = tank_limit
        self.memo = memo
        self.pingable = pingable

    def _find_user(self, user_id):
        """Return (bucket_name, msg) for any user in the roster."""
        uid = str(user_id)
        for attr in [
            "dps",
            "healers",
            "tanks",
        ]:
            bucket = getattr(self, attr)
            if uid in bucket:
                return attr, bucket[uid]
        return None, None

    def _remove_from_bucket(self, bucket_name, user_id):
        del getattr(self, bucket_name)[str(user_id)]

    def add_member(self, user_id, role, msg=""):
        """
        :return
            0 = added to main
            1 = invalid role
        """
        user_id = str(user_id)
        if role not in self.role_map:
            return 1

        old_msg, old_role, _ = self.remove_member(user_id, need_vals=True)
        if msg == "" and old_msg != "" and old_role == role:
            msg = old_msg

        bucket = getattr(self, role)

        bucket[user_id] = msg
        return 0

    def remove_member(self, user_id, need_vals=False):
        """Wrapper that finds the member, removes them correctly, and returns info."""
        user_id = str(user_id)
        bucket_name, msg = self._find_user(user_id)

        if bucket_name is None:
            return False if not need_vals else ("", "", False)

        # Identify role
        if bucket_name in ["dps", "backup_dps", "overflow_dps"]:
            role = "dps"
        elif bucket_name in ["healers", "backup_healers", "overflow_healers"]:
            role = "healer"
        else:
            role = "tank"

        # Only fill overflow if removing from main
        main_attr, _, _ = self.role_map[role]
        if bucket_name == main_attr:
            self._remove_from_bucket(bucket_name, user_id)
            self.overflow_fill(role)
        else:
            self._remove_from_bucket(bucket_name, user_id)

        if need_vals:
            return msg, role, True
        return True

    def update_message(self, user_id, new_message):
        uid = str(user_id)
        bucket_name, _ = self._find_user(uid)
        if bucket_name is None:
            return False
        getattr(self, bucket_name)[uid] = new_message
        return True

    def swap_people(self, user_id_1, user_id_2):
        user_id_1 = str(user_id_1)
        user_id_2 = str(user_id_2)

        b1, msg1 = self._find_user(user_id_1)
        if b1 is None:
            return False  # user 1 must exist

        b2, msg2 = self._find_user(user_id_2)

        # Remove user 1
        del getattr(self, b1)[user_id_1]

        if b2 is None:
            # User 2 not found: just remove user 1 as they are swapping out
            return True

        # Swap between two in a roster.
        del getattr(self, b2)[user_id_2]
        getattr(self, b1)[user_id_2] = msg2
        getattr(self, b2)[user_id_1] = msg1
        return True

    def fill_spots(self):
        try:
            for role, (main_attr, backup_attr, overflow_attr) in self.role_map.items():
                main = getattr(self, main_attr)
                backup = getattr(self, backup_attr)
                overflow = getattr(self, overflow_attr)
                limit = getattr(self, f"{role}_limit")

                while True:
                    if len(main) < limit and overflow:
                        first = next(iter(overflow))
                        main[first] = overflow[first]
                        del overflow[first]
                    elif len(main) < limit and not overflow and backup:
                        first = next(iter(backup))
                        main[first] = backup[first]
                        del backup[first]
                    else:
                        break
            return True
        except Exception as e:
            logging.error(f"Fill Spots error: {str(e)}")
            return False

    def overflow_fill(self, role):
        if role not in self.role_map:
            return
        main_attr, _, overflow_attr = self.role_map[role]
        main = getattr(self, main_attr)
        overflow = getattr(self, overflow_attr)
        limit = getattr(self, f"{role}_limit")

        while len(main) < limit and overflow:
            first = next(iter(overflow))
            main[first] = overflow[first]
            del overflow[first]

    def did_values_change(self, old_roster):
        for key, value in vars(self).items():
            if value != getattr(old_roster, key, None):
                return True
        return False

    def push_excess_to_overflow(self):
        """
        Move members from main roster to overflow if the main roster exceeds its role limit.
        Preserves the original order of members.
        """
        role_attrs = {
            "dps": ("dps", "overflow_dps"),
            "healer": ("healers", "overflow_healers"),
            "tank": ("tanks", "overflow_tanks"),
        }

        moved_summary = {}

        for role, (main_attr, overflow_attr) in role_attrs.items():
            main_bucket = getattr(self, main_attr)
            overflow_bucket = getattr(self, overflow_attr)
            limit = getattr(self, f"{role}_limit")

            to_remove = max(len(main_bucket) - limit, 0)

            if to_remove > 0:
                # Take last n members that are now over limit
                last_members = list(main_bucket.items())[-to_remove:]

                # Remove from main
                for user_id, _ in last_members:
                    del main_bucket[user_id]

                # Add to start of overflow to preserve order
                for user_id, msg in reversed(last_members):
                    overflow_bucket.update({user_id: msg})

                moved_summary[role] = [user_id for user_id, _ in last_members]

        return moved_summary

    def get_roster_data(self):
        data = {
            "trial": self.trial,
            "date": self.date,
            "leader": self.leader,
            "dps": self.dps,
            "healers": self.healers,
            "tanks": self.tanks,
            "backup_dps": self.backup_dps,
            "backup_healers": self.backup_healers,
            "backup_tanks": self.backup_tanks,
            "overflow_dps": self.overflow_dps,
            "overflow_healers": self.overflow_healers,
            "overflow_tanks": self.overflow_tanks,
            "dps_limit": self.dps_limit,
            "healer_limit": self.healer_limit,
            "tank_limit": self.tank_limit,
            "role_limit": self.role_limit,
            "memo": self.memo,
            "pingable": self.pingable,
        }
        return data
