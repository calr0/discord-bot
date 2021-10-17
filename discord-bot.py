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

    @staticmethod
    def log(message: str, level=logging.INFO):
        logger.write(message, level)

    @utils.logger
    def run(self):
        return super().run(self.token)

    @utils.logger
    async def on_ready(self):
        guild = discord.utils.find(lambda g: g.name == self.server, self.guilds)
        salbot.log(f"{self.user.name} connected to '{guild.name}' ({guild.id})")
        for member in guild.members:
            logger.write(f"Found member: {member.name}", logging.INFO)

    async def on_typing(self, channel, user, when):
        salbot.log(f"{user.name} is typing in {channel} during {when}")

    async def on_message(self, message):
        content = message.content
        author = message.author
        channel = message.channel

        salbot.log(f"{author.name} posted message in {channel}: {content}")

        if content == "!test":
            await channel.send("test response")
        elif content == "!asdf":

            def check_response(m, resp):
                return m.content == resp and m.channel == channel

            msg = await self.wait_for("message", check=lambda m: check_response(m, "asdf"))
            await channel.send(f"Hello {msg.author.name}")


if __name__ == "__main__":
    discord.Intents.all()
    utils.init_logging()
    dotenv.load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD = os.getenv("DISCORD_GUILD")
    bot_client = salbot(TOKEN, GUILD)
    bot_client.run()
