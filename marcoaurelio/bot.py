import re
import env
import random
import string
import discord
import embeds.help as help_embed

from math import floor
from dotmap import DotMap
from marcoaurelio.session import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class MarcoAurelio(discord.Client):

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
        response = await cmd_handler(context, args)

        await message.channel.send(response)

    async def _cmd_config(self, context, args):
        if len(args) < 2:
            return 'Invalid number of parameters'

        uuid = args.pop(0)

        if uuid not in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]
        session.config(args)

        return f'Session **`{uuid}`** correctly configured!'

    async def _cmd_help(self, context, args):
        embed = discord.Embed(title=help_embed.TITLE,
                              description=help_embed.DESCRIPTION,
                              color=help_embed.COLOR)
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
            return 'Invalid number of parameters'

        if len(args) <= 0:
            uuid = self._new_uuid()
            while uuid in self._sessions:
                uuid = self._new_uuid()
        else:
            uuid = args[0]
            if uuid in self._sessions:
                return f'Session **`{uuid}`** already exists!'

        self._sessions[uuid] = Session(uuid)

        return f'Your session UUID is **`{uuid}`**'

    async def _cmd_start(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if uuid not in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]
        context.session = session

        try:
            session.start()
            response = f'Session **`{uuid}`** has started!'

            self._scheduler.add_job(func=self._sched_info,
                                    args=(context,),
                                    trigger='interval',
                                    seconds=env.SESSION_INFO_INTERVAL,
                                    id=session.name())
            self._scheduler.start()
        except RuntimeError as err:
            response = f'Error: {err}'

        return response

    async def _cmd_stop(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if uuid not in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]
        session.stop()

        self._scheduler.remove_job(session.name())

        return f'Session **`{uuid}`** has been stopped!'

    async def _cmd_remove(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if uuid not in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        del self._sessions[uuid]

        return f'Session **`{uuid}`** has been correctly deleted!'

    async def _sched_info(self, context):
        block = context.session.current_block()

        if context.session.active():
            m, s = divmod(block.remaining(), 60)
            h, m = divmod(m, 60)

            message = f'Session `{context.session.name()}` | ' \
                      f'Block `{block.name()}` | ' \
                      f'Remaining time: **{h:02d}:{m:02d}:{s:02d}**'

            await context.channel.send(message)
        else:
            self._scheduler.remove_job(context.session.name())

    def _new_uuid(self, numchar=32):
        _id = ''.join(random.choice(string.ascii_uppercase +
              string.ascii_lowercase + string.digits) for _ in range(32))
        return _id
