import logging
import logging.config
import string
# import aiohttp

from dc.bot_manager import *
from discord.ext import commands
# from lib import *
from log_config import *
# from nova.discord_types import BOT

bot = BOT.create_bot()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = Game('Ready for Screenshots')

    try:
        await bot.change_presence(status=Status.online, activity=game)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print(traceback.format_exc())


@bot.event
async def on_message(message):
    try:
        print(f'Event on_message: author {message.author}')
        # Return if bot's own message
        if message.author == bot.user:
            return

        # print(f'  message: {message.content}')
        # await bot.process_commands(message)
        # print(f'Event on_message: process_commands complete')

        # if len(message.attachments) == 0:
        #     print(f'Event on_message: no attachments to process')

        # # If the message has attachments
        # if len(message.attachments) > 0:
        #     print(f'Event on_message: handle_attachments')
        #     await handle_attachments(message)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print(traceback.format_exc())
        await ctx.send(content=str(err))

    print(f'on_message: complete')

    return

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    try:
        print(f'Event on_reaction_add: user {user}')
        # Return if bot's own message
        if user == bot.user:
            return

        # print(f'  emoji: {reaction.emoji} {type(reaction.emoji)}')
        # if isinstance(reaction.emoji, discord.Emoji):
        #     print(f'  message: {reaction.emoji.id}')
        # if reaction.emoji == '🔄':
        #     print(f'  YAY')

        # return

        # message = reaction.message
        # if len(message.attachments) == 0:
        #     print(f'Event on_reaction_add: no attachments to process')

        # # If the message has attachments
        # if len(message.attachments) == 1:
        #     print(f'Event on_reaction_add: handle_attachments')
        #     await handle_attachments(message)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print(traceback.format_exc())
        await message.channel.send(content=str(err))

    print(f'on_message: complete')

    return

@bot.event
async def on_guild_join(guild):
    message = reaction.message
    try:
        print(f'on_guild_join: guild {guild}')
        # Return if bot's own message
        # if user == bot.user:
        #     return

        # print(f'  emoji: {reaction.emoji} {type(reaction.emoji)}')
        # if isinstance(reaction.emoji, discord.Emoji):
        #     print(f'  message: {reaction.emoji.id}')
        # if reaction.emoji == '🔄':
        #     print(f'  YAY')

        # return

        # message = reaction.message
        # if len(message.attachments) == 0:
        #     print(f'Event on_reaction_add: no attachments to process')

        # # If the message has attachments
        # if len(message.attachments) == 1:
        #     print(f'Event on_reaction_add: handle_attachments')
        #     await handle_attachments(message)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print(traceback.format_exc())
        await message.channel.send(content=str(err))

    print(f'on_message: complete')

    return

BOT.run_bot()
