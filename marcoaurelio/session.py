import time
import datetime

from math import inf as INF
from marcoaurelio.block import Block
from apscheduler.schedulers.background import BackgroundScheduler


class Session:

    _schedjob_id = '__block_sched'

    def __init__(self, name='__session', timefunc = time.monotonic):
        self._start_time = INF
        self._name = name
        self._blocks = []
        self._curr_block = -1;

        self._timefunc = timefunc
        self._scheduler = BackgroundScheduler(daemon=True)

    def name(self):
        return self._name

    def finished(self):
        return self._curr_block >= len(self._blocks)

    def current_block(self):
        if self._curr_block >= 0 and self._curr_block < len(self._blocks):
            return self._blocks[self._curr_block]
        else:
            return None

    def start(self):
        if len(self._blocks) <= 0:
            raise RuntimeError('no blocks to start!')

        self._start_time = self._timefunc()

        self._scheduler.start()
        self.next()

    def stop(self):
        if not self.finished():
            self._scheduler.remove_all_jobs()
            self._scheduler.shutdown()

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
                name = f'_block_{i}'
            except ValueError:
                name = arg

    def next(self):
        # Stop current block
        if self._curr_block >= 0:
            self._blocks[self._curr_block].stop()

        # Advance to next block
        self._curr_block += 1

        # Continue only if there are more blocks pending
        if self._curr_block < len(self._blocks):
            curr_block = self._blocks[self._curr_block]
            curr_block.start()

            run_date = datetime.datetime.now() + \
                       datetime.timedelta(seconds=curr_block.duration())

            self._scheduler.add_job(func=self.next,
                                    trigger='date',
                                    run_date=run_date,
                                    id=Session._schedjob_id)
