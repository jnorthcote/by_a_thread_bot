import base64
import json
import os
import time
import traceback

from copy import deepcopy
from datetime import datetime
from discord import Intents, Game, Status, Emoji, Embed
from discord.ext import commands

from log_config import *

logger = get_logger(__name__)

class BotRef():
    def __init__(self):
        self.bot = None
        self.bot_token = None
        self.client_id = None
        self.command_prefix = '!'

    def create_bot(self):

        intents = Intents.default()
        intents.guilds = True
        intents.message_content = True
        intents.reactions = True

        self.get_bot_config()
        print(f'Using command prefix: {self.command_prefix}')
        self.bot = commands.Bot(command_prefix = self.command_prefix, intents=intents)

        return self.bot

    def get_bot_config(self):

        # Load config keys
        with open('config.json', 'r') as f:
            config = json.load(f)

        if 'prefix-key' in config:
            self.command_prefix = config['prefix-key']

        bot_token = os.getenv('DISCORD_BOT_TOKEN')
        # client_id = os.getenv('DISCORD_CLIENT_ID')

        if bot_token is None:
            with open('discord_secrets.json', 'r') as f:
                discord_secrets = json.load(f)

            if 'discord-token' in discord_secrets:
                bot_token = discord_secrets['discord-token']
        # else:
        #     bot_token = str(base64.b64decode(str(bot_token_b64)))

        logger.info(f"bot_token {bot_token=}")
        self.bot_token = bot_token
        # self.client_id = client_id

    def run_bot(self):
        self.bot.run(self.bot_token)

BOT = BotRef()
