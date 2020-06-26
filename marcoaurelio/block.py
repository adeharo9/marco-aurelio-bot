import time

from math import inf as INF


class Block:

    def __init__(self, duration, name='__block', timefunc = time.monotonic):
        self._duration = duration
        self._name = name
        self._start_time = INF
        self._end_time = -INF
        self._stop_time = -INF

        self._timefunc = timefunc

    def duration(self):
        return self._duration

    def remaining(self):
        return self._end_time - self._timefunc()

    def start_time(self):
        return self._start_time

    def end_time(self):
        return self._end_time

    def name(self):
        return self._name

    def active(self):
        curr_time = self._timefunc()
        return curr_time > self._start_time and curr_time < self._end_time

    def start(self):
        self._start_time = self._timefunc()
        self._end_time = self._start_time + self._duration

    def stop(self):
        self._stop_time = self._timefunc()
