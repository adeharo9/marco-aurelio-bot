import re
import env
import random
import string
import utils.uuid as uuid
import strings.help as help_embed
import strings.error as error_str

from dotmap import DotMap
from discord import Embed
from discord import Client
from marcoaurelio.session import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from marcoaurelio.exceptions import Error, InvalidNArgsError, NotFoundError, \
                                    AlreadyFoundError


class MarcoAurelio(Client):

    def __init__(self, cmd_prefix='!'):
        self._sessions = {}

        self._cmd_prefix = cmd_prefix
        self._cmd_handlers = {
            'config': self._cmd_config,
            'help': self._cmd_help,
            'new': self._cmd_new,
            'remove': self._cmd_remove,
            'start': self._cmd_start,
            'stop': self._cmd_stop
        }

        self._scheduler = AsyncIOScheduler()

        super().__init__()

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'{self.user} is connected to the following guilds:')
        for guild in self.guilds:
            print(f'    {guild.id} - {guild.name}')

    async def on_message(self, message):
        if not message.content.startswith(self._cmd_prefix) or \
           message.author == self.user:
            return

        context = DotMap()
        context.guild = message.guild
        context.channel = message.channel

        args = message.content[len(self._cmd_prefix):]
        args = re.split(' +', args)
        command = args.pop(0).lower()

        cmd_handler = self._cmd_handlers.get(command, lambda *_: None)

        try:
            await cmd_handler(context, args)
        except Error as err:
            await context.channel.send(str(err))

    async def _cmd_config(self, context, args):
        if len(args) < 2:
            raise InvalidNArgsError('!config', 'at least 2', len(args))

        _uuid = args.pop(0)

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]
        session.config(args)

        await context.channel.send(f'Session **`{_uuid}`** correctly configured!')

    async def _cmd_help(self, context, args):
        embed = Embed(title=help_embed.TITLE,
                      description=help_embed.DESCRIPTION.format(
                          self.user.display_name),
                      url=help_embed.URL,
                      color=help_embed.COLOR)
        embed.set_footer(icon_url=help_embed.FOOTER_ICON_URL,
                         text=help_embed.FOOTER_TEXT)
        embed.set_thumbnail(url=help_embed.THUMBNAIL_URL)
        embed.set_author(name=help_embed.AUTHOR_NAME.format(
                          self.user.display_name),
                         url=help_embed.AUTHOR_URL,
                         icon_url=help_embed.AUTHOR_ICON_URL)
        embed.add_field(name=help_embed.F1_NAME,
                        value=help_embed.F1_VALUE,
                        inline=help_embed.F1_INLINE)
        embed.add_field(name=help_embed.F2_NAME,
                        value=help_embed.F2_VALUE,
                        inline=help_embed.F2_INLINE)
        embed.add_field(name=help_embed.F3_NAME,
                        value=help_embed.F3_VALUE,
                        inline=help_embed.F3_INLINE)
        embed.add_field(name=help_embed.F4_NAME,
                        value=help_embed.F4_VALUE,
                        inline=help_embed.F4_INLINE)
        embed.add_field(name=help_embed.F5_NAME,
                        value=help_embed.F5_VALUE,
                        inline=help_embed.F5_INLINE)
        await context.channel.send(embed=embed)

    async def _cmd_new(self, context, args):
        if len(args) > 1:
            raise InvalidNArgsError('!new', 'at most 1', len(args))

        if len(args) <= 0:
            _uuid = uuid.new()
            while _uuid in self._sessions:
                _uuid = uuid.new()
        else:
            _uuid = args[0]
            if _uuid in self._sessions:
                raise AlreadyFoundError(f'Session **`{_uuid}`** already exists!')

        self._sessions[_uuid] = Session(_uuid)

        await context.channel.send(f'Your session UUID is **`{_uuid}`**')

    async def _cmd_start(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!start', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]
        context.session = session

        await context.channel.send(f'Session **`{_uuid}`** has started!')

        if not self._scheduler.running:
            self._scheduler.start()

        session.start()
        self._scheduler.add_job(func=self._sched_info,
                                args=(context,),
                                trigger='interval',
                                seconds=env.SESSION_INFO_INTERVAL,
                                id=session.name())

        await self._sched_info(context)

    async def _cmd_stop(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!stop', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]
        session.stop()

        self._scheduler.remove_job(session.name())

        await context.channel.send(f'Session **`{_uuid}`** has been stopped!')

    async def _cmd_remove(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!remove', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        del self._sessions[_uuid]

        await context.channel.send(f'Session **`{_uuid}`** has been correctly deleted!')

    async def _sched_info(self, context):
        block = context.session.current_block()

        if context.session.active():
            m, s = divmod(round(block.remaining()), 60)
            h, m = divmod(m, 60)

            message = f'Session `{context.session.name()}` | ' \
                      f'Block `{block.name()}` | ' \
                      f'Remaining time: **{h:02d}:{m:02d}:{s:02d}**'

            await context.channel.send(message)
        else:
            self._scheduler.remove_job(context.session.name())
