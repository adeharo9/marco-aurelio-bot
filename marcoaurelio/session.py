import time
import datetime

from math import inf as INF
from apscheduler.schedulers.background import BackgroundScheduler

from .block import Block
from .exceptions import NotFoundError


class Session:

    _schedjob_id = '__block_sched'

    def __init__(self, name='__session', timefunc=time.monotonic):
        self._start_time = INF
        self._name = name
        self._blocks = []
        self._curr_block = -1
        self._running = False

        self._timefunc = timefunc
        self._scheduler = BackgroundScheduler()

    def name(self):
        return self._name

    def active(self):
        return self._running

    def current_block(self):
        if self._curr_block >= 0 and self._curr_block < len(self._blocks):
            return self._blocks[self._curr_block]
        else:
            return None

    def start(self):
        if len(self._blocks) <= 0:
            raise NotFoundError('No blocks to start!')

        self._start_time = self._timefunc()

        if not self._scheduler.running:
            self._scheduler.start()

        self._curr_block = -1
        self._running = True
        self.next()

    def stop(self):
        self._scheduler.remove_all_jobs()

        if self._scheduler.running:
            self._scheduler.shutdown()

        self._running = False

    def config(self, args):
        i = 0
        name = f'__block_{i}'
        for arg in args:
            try:
                duration_s = int(arg) * 60
                block = Block(duration=duration_s,
                              name=name)
                self._blocks.append(block)

                i += 1
                name = f'__block_{i}'
            except ValueError:
                name = arg

    def next(self):
        # Stop current block
        if self._curr_block >= 0:
            self._blocks[self._curr_block].stop()

        # Advance to next block
        self._curr_block += 1

        # Continue only if there are more blocks pending
        if self._curr_block >= 0 and self._curr_block < len(self._blocks):
            curr_block = self._blocks[self._curr_block]
            curr_block.start()

            run_date = datetime.datetime.now() + \
                datetime.timedelta(seconds=curr_block.duration())

            self._scheduler.add_job(func=self.next,
                                    trigger='date',
                                    run_date=run_date,
                                    id=Session._schedjob_id)
        else:
            self._running = False
