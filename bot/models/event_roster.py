class EventRoster:
    def __init__(self, event, date, leader, memo, pingable, members=None):
        self.event = event
        self.date = date
        self.leader = leader
        self.memo = memo
        self.pingable = pingable
        self.members = members or {}

    def get_roster_data(self):
        all_data = {
            "event": self.event,
            "date": self.date,
            "leader": self.leader,
            "memo": self.memo,
            "pingable": self.pingable,
            "members": self.members,
        }
        return all_data

    def add_member(self, user_id, msg=""):
        self.members[user_id] = msg

    def remove_member(self, user_id):
        if user_id in self.members:
            del self.members[user_id]
            return True
        return False

    def update_message(self, user_id, new_message):
        if user_id in self.members.keys():
            self.members[user_id] = new_message
            return True
        return False
