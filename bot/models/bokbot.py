from discord.ext import commands
from bot.database import Librarian, init_librarian


class BOKBot(commands.Bot):
    def __init__(self, config: dict, rosters: dict, language: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config: dict = config
        self.librarian: Librarian = init_librarian(config["bot"]["mongo"])
        self.rosters: dict = rosters
        self.language: dict = language
        self.limits: list = []
