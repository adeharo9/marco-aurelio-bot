import re
import random
import string
import discord

from math import floor
from marcoaurelio.session import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class MarcoAurelio(discord.Client):

    _schedjob_id = '__session_sched'
    
    def __init__(self, channel):
        self._channel = channel

        self._cmd_prefix = '!'
        self._sessions = {}

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
            print(f'\t{guild.id} - {guild.name}')

    async def on_message(self, message):
        if not message.content.startswith(self._cmd_prefix) or message.author == self.user:
            return

        context = {
            'guild': message.guild,
            'channel': message.channel
        }

        args = message.content[len(self._cmd_prefix):];
        args = re.split(' +', args)
        command = args.pop(0).lower();

        cmd_handler = self._cmd_handlers.get(command, lambda *_: None)
        response = await cmd_handler(context, args)

        await message.channel.send(response)

    async def _cmd_config(self, context, args):
        if len(args) < 1:
            return 'Invalid number of parameters'

        uuid = args.pop(0)

        if not uuid in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]

        session.config(args)

        return f'Session **`{uuid}`** correctly configured!'

    async def _cmd_help(self, context, args):
        response = 'Under development'

        return response

    async def _cmd_new(self, context, args):
        if len(args) > 1:
            return 'Invalid number of parameters'

        if len(args) == 0:
            uuid = self._new_uuid()
        elif len(args) == 1:
            uuid = args[0]

        if uuid in self._sessions:
            return f'Session **`{uuid}`** already exists!'

        self._sessions[uuid] = Session(uuid)

        return f'Your session UUID is **`{uuid}`**'

    async def _cmd_start(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if not uuid in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]
        context['session'] = session

        try:
            session.start()
            response = f'Session **`{uuid}`** has started!'

            self._scheduler.add_job(func=self._sched_info,
                                    args=(context,),
                                    trigger='interval',
                                    seconds=60,
                                    id=session.name())
            self._scheduler.start()
        except RuntimeError as err:
            response = f'Error: {err}'

        return response

    async def _cmd_stop(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if not uuid in self._sessions:
            return f'Session **`{uuid}`** does not exist!'

        session = self._sessions[uuid]

        try:
            session.stop()
            response = f'Session **`{uuid}`** has been stopped!'

            self._scheduler.remove_job(session.name())
        except RuntimeError as err:
            response = f'Error: {err}'

        return response

    async def _cmd_remove(self, context, args):
        if len(args) != 1:
            return 'Invalid number of parameters'

        uuid = args[0]

        if uuid in self._sessions:
            del self._sessions[uuid]
            response = f'Session **`{uuid}`** has been correctly deleted!'
        else:
            response = f'Session **`{uuid}`** does not exist!'

        return response

    async def _sched_info(self, context):
        session = context['session']
        block = session.current_block()

        if block is not None:
            dec_hours = block.remaining() / 3600
            hours = floor(dec_hours)

            dec_minutes = (dec_hours - hours) * 60
            minutes = floor(dec_minutes)

            dec_seconds = (dec_minutes - minutes) * 60
            seconds = floor(dec_seconds)

            message = f'Session `{session.name()}` | ' \
                    f'Block `{block.name()}` | ' \
                    f'Remaining time: **{hours}:{minutes}:{seconds}**'

            await context['channel'].send(message)
        else:
            self._scheduler.remove_job(session.name())

    def _new_uuid(self, numchar=32):
        _id = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))
        return _id
