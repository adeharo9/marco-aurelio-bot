import re
import dotenvpy as env

from dotmap import DotMap
from discord import Client, Embed
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .utils import uuid
from .session import Session
from .strings import help as help_embed
from .exceptions import Error, InvalidNArgsError, NotFoundError, \
                        AlreadyFoundError, NotRunningError, \
                        AlreadyRunningError


class MarcoAurelio(Client):

    def __init__(self, cmd_prefix='!'):
        self._sessions = {}

        self._cmd_prefix = cmd_prefix
        self._cmd_handlers = {
            'config': self._cmd_config,
            'help': self._cmd_help,
            'new': self._cmd_new,
            'remaining': self._cmd_remaining,
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

        await context.channel.send(f'Session **`{_uuid}`** correctly '
                                   'configured!')

    async def _cmd_help(self, context, args):
        embed = Embed(title=help_embed.TITLE,
                      description=help_embed.DESCRIPTION.format(
                          self.user.display_name),
                      url=help_embed.URL,
                      color=help_embed.COLOR)
        embed.set_footer(icon_url=str(self.user.avatar_url),
                         text=help_embed.FOOTER_TEXT)
        embed.set_thumbnail(url=str(self.user.avatar_url))
        embed.set_author(name=help_embed.AUTHOR_NAME.format(
                          self.user.display_name),
                         url=help_embed.AUTHOR_URL,
                         icon_url=str(self.user.avatar_url))
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
        embed.add_field(name=help_embed.F6_NAME,
                        value=help_embed.F6_VALUE,
                        inline=help_embed.F6_INLINE)
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
                raise AlreadyFoundError(f'Session **`{_uuid}`** already '
                                        'exists!')

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

        if session.active():
            raise AlreadyRunningError(f'Session **`{_uuid}`** is already '
                                      'running!')

        if not self._scheduler.running:
            self._scheduler.start()

        session.start()
        self._scheduler.add_job(func=self._on_interval,
                                args=(context,),
                                trigger='interval',
                                seconds=env.SESSION_INFO_INTERVAL,
                                id=session.name())

        await context.channel.send(f'Session **`{_uuid}`** has started!')
        await self._on_interval(context)

    async def _cmd_stop(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!stop', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]

        if not session.active():
            raise NotRunningError(f'Session **`{_uuid}`** is not running!')

        job = self._scheduler.get_job(session.name())
        if job is None:
            raise RuntimeError(f'Session **`{_uuid}`** is running but has no '
                               'job assigned!')

        session.stop()
        self._scheduler.remove_job(job.id)

        await context.channel.send(f'Session **`{_uuid}`** has been stopped!')

    async def _cmd_remove(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!remove', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]

        if session.active():
            await self._cmd_stop(context, [_uuid])

        del self._sessions[_uuid]

        await context.channel.send(f'Session **`{_uuid}`** has been correctly '
                                   'deleted!')

    async def _cmd_remaining(self, context, args):
        if len(args) != 1:
            raise InvalidNArgsError('!remaining', 'exactly 1', len(args))

        _uuid = args[0]

        if _uuid not in self._sessions:
            raise NotFoundError(f'Session **`{_uuid}`** does not exist!')

        session = self._sessions[_uuid]
        context.session = session

        await self._send_remaining(context)

    async def _send_remaining(self, context):
        if not context.session.active():
            raise NotRunningError(f'Session **`{context.session.name()}`** is '
                                  'not running!')

        block = context.session.current_block()
        m, s = divmod(round(block.remaining()), 60)
        h, m = divmod(m, 60)

        message = f'Session `{context.session.name()}` | ' \
            f'Block `{block.name()}` | ' \
            f'Remaining time: **{h:02d}:{m:02d}:{s:02d}**'

        await context.channel.send(message)

    async def _on_interval(self, context):
        if context.session.active():
            await self._send_remaining(context)
        else:
            job = self._scheduler.get_job(context.session.name())
            if job is not None:
                self._scheduler.remove_job(job.id)
