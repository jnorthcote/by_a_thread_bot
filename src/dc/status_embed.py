import base64
import json
import os
import time
import traceback

# from copy import deepcopy
# from datetime import datetime
from discord import Intents, Game, Status, Emoji, Embed
# from discord.ext import commands
from enum import Enum
# from nova.entity import EmbedField
from log_config import *

logger = get_logger(__name__)

class StatusTypeEnum(bytes, Enum):

    def __new__(cls, value, label, emoji):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.label = label
        obj.emoji = emoji
        return obj

    info = (0, 'Informational','⚫')
    good = (1, 'Success', '🟢')
    warn = (2, 'Warnings', '🟡')
    fail = (3, 'Failure', '🔴')
    inputs = (4, 'Input Needed', '❔')
    alert = (5, 'Alert', '❗')
    passed = (6, 'Valid', '✅')
    in_vars= (7, 'In up', '⏫')

class StatusEmbed():
    def __init__(self, message, title = 'Upload Status', description = 'Preparing...', color = 0x0025ff):

        self.message = message
        self.embed_message = None

        self.title   = title
        self.color   = color
        self.description = [description]

        self.message_options = None
        self.attachments = []
        self.fields = {}
        self.answers = {}

    async def post_embed(self):

        new_message = None
        try:
            embed = to_embed(title = self.title, description = '\n'.join(self.description), color = self.color, fields = self.fields)
            embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/1105433922344599563/1105433972902727732/bar.png')
            # embed.set_image(url = 'https://cdn.discordapp.com/attachments/1105433922344599563/1106071459517968454/bar-h.png')
            if len(self.attachments)>0:
                embed.set_image(url = self.attachments[-1]['url'])

            if self.embed_message is None:
                new_message = await self.message.channel.send(None, embed=embed)
            else:
                new_message = await self.embed_message.edit(embed=embed)

            self.embed_message = new_message

        except Exception as err:
            logger.warn(f"Exception {err=}, {type(err)=}")
            logger.warn(traceback.format_exc())

        return self

    def add_desc(self, description, status = StatusTypeEnum.info):
        new_desc = f'{status.emoji} {description}'
        self.description.append(new_desc)
        return self

    def add_message_options(self, message_options):
        try:
            # if self.message_options is None:
            self.message_options = message_options
                # self.description.append(f'Flags : `{self.message_options.flags}`')
                # self.description.append(f'Fields: `{self.message_options.fields}`')
        except Exception as err:
            logger.warn(f"Exception {err=}, {type(err)=}")
            logger.warn(traceback.format_exc())

        return self

    def add_attachment(self, url=None, name=None):
        self.attachments.append({'url':url, 'name':name})
        self.add_desc(f'Attachment : [{name}]({url})')

        return self

    def add_ss_match(self, ss_match=None):
        attachment = self.attachments[-1]
        self.add_desc(f'{ss_match.ss_type.label} Matches!', status = StatusTypeEnum.good)
        attachment['ss_match'] = ss_match
        return self

    async def check_inputs(self):
        attachment = self.attachments[-1]
        ss_match = attachment['ss_match']

        if len(ss_match.ss_type.inputs)>0:
            in_var_channel = self.message.channel

            def check(author):
                def inner_check(message):
                    logger.debug(f'inner_check - author: {author} in_var_channel: {in_var_channel}')
                    return message.author == author and message.channel == in_var_channel

                return inner_check

            var_values = {}
            await self.add_desc(f'{ss_match.ss_type.label} has {len(ss_match.ss_type.inputs)} inputs: {ss_match.ss_type.inputs}', status = StatusTypeEnum.inputs).post_embed()

            for input_var in ss_match.ss_type.inputs:
                if input_var not in self.answers:
                    await self.add_desc(f'**{StatusTypeEnum.inputs.label}** Please provide a value for *{input_var}*', status = StatusTypeEnum.inputs).post_embed()
                    input_msg = await BOT.bot.wait_for('message', check=check(self.message.author), timeout=30)
                    if input_msg != None and len(input_msg.content)>0:
                        var_values[input_var] = input_msg

                        # await self.add_desc(f'Using **{input_msg.content}** for *{input_var}*', status = StatusTypeEnum.good)
            vars_field = []
            for var_name, value in var_values.items():
                vars_field.append(f'{StatusTypeEnum.in_vars.emoji} **{value.content}** provided for *{var_name}* ')
                self.answers[var_name] = value.content
                await value.delete()

            self.fields[f'{StatusTypeEnum.passed.emoji} Input Variables'] = '\n'.join(vars_field)
            await self.post_embed()

            for input_var in ss_match.ss_type.inputs:
                if input_var not in self.message_options.fields:
                    self.message_options.fields[input_var] = self.answers[input_var]

        return


    def finish_attachment(self, output, status = StatusTypeEnum.good):
        attachment = self.attachments[-1]
        attachment['status'] = status

        match_type = 'No matches'
        if 'ss_match' in attachment:
            match_type = attachment["ss_match"].ss_type.label

        self.fields[f'{status.emoji} {attachment["name"]} [{match_type}]'] = output
        return self

    async def cleanup(self):
        all_good = True
        for att in self.attachments:
            if 'status' not in att or att['status'] == StatusTypeEnum.fail:
                all_good = False
                break

        if all_good:
            for att in self.attachments:
                await BOT.bot.get_channel(1105724589331464222).send(att['url'])
                # await send_message(att['url'], BOT.bot.get_channel(1105724589331464222), None)
            await self.message.delete()

