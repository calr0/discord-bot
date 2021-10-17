import os
import discord
import dotenv
import utils
import logging

from utils.logger import logger


class salbot(discord.Client):
    @utils.logger
    def __init__(self, token, guild_name):
        super().__init__()
        self.token = token
        self.server = guild_name

    @utils.logger
    def run(self):
        return super().run(self.token)

    @utils.logger
    async def on_ready(self):
        guild = discord.utils.find(lambda g: g.name == self.server, self.guilds)
        logger.write(f"{self.user} connected to '{guild.name}' ({guild.id})", logging.INFO)

    async def on_message(self, message):
        msg = "Message from {0.author}: {0.content}".format(message)
        logger.write(msg, logging.INFO)


if __name__ == "__main__":
    utils.init_logging()
    dotenv.load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD = os.getenv("DISCORD_GUILD")
    bot_client = salbot(TOKEN, GUILD)
    bot_client.run()
