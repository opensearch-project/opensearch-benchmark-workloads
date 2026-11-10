# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""``"schedule": "shape"``: one OSB task whose load follows a load shape (load_shape.py), with no restart.

The task's ``shape`` parameter picks the mode:

* **QPS shape** (``unit: "qps"``, ``max`` = peak rate): every client sends at ``rate(t) / clients``. When the
  clients can't keep that rate (each one skips more than ``limitFraction`` of its slots over
  ``limitWindowS``), the task ends early and logs ``SHAPE_CLIENT_LIMITED``: the peak needs more clients or a
  bigger client machine, and everything before that point is a valid result.
* **Client shape** (``unit: "clients"``, ``max`` = peak active clients): ``round(level(t) * max)`` clients send
  back to back at full speed; the others wait until the shape needs them.
* **Client shape, no max**: as above, with ``max`` = the task's clients (set them to the client machine's
  cores).

The task ends when the shape does (every client stops at the shape's end), so set ``time-period`` to at
least the shape's duration. Warmup (``warmup-time-period``) runs at the shape's starting level and is not
part of the shape's time.

Late slots are skipped, not caught up: OSB sends a request whose scheduled time has passed at once, so a
client that fell behind at a peak would otherwise keep firing after it and smear the shape. Each client logs
``SHAPE_PROGRESS`` every 60 s and ``SHAPE_END`` when it stops, with its slots and skipped slots.
"""
import logging
import random
import time
from collections import deque

from . import load_shape

FLOOR_QPS = 1e-3          # per-client rates below this are treated as "off"
SCAN_S = 1.0              # resolution when looking for the next time a client is needed


class ShapeScheduler:
    def __init__(self, task):
        self.logger = logging.getLogger(__name__)
        self.task = task
        self.shape = load_shape.parse(task.params.get("shape"))
        self.unit = self.shape["unit"]
        self.clients = max(int(task.clients or 1), 1)
        mx = self.shape.get("max")
        if self.unit == "clients":
            mx = self.clients if mx is None else min(int(mx), self.clients)
        self.max = float(mx)
        self.warmup = float(task.warmup_time_period or 0)
        self.end = self.warmup + load_shape.duration(self.shape)
        self.limit_fraction = float(self.shape.get("limitFraction", 0.1))
        self.limit_window = float(self.shape.get("limitWindowS", 60))
        self.stop_when_limited = bool(self.shape.get("stopWhenLimited", True))
        # OSB injects the task's (partitioned) parameter source here before the first next()
        self.parameter_source = None
        self.index = None
        self.t0 = None              # perf_counter at the task's time 0, from the first before_request
        self.first = None           # the first slot returned
        self.slots = self.skipped = 0
        self.recent = deque()       # (shape time, slots, skipped) per slot, for the limit check
        self.last_progress = 0.0
        self.stopped = False

    # ---- OSB scheduler API -------------------------------------------------------------------------------

    def before_request(self, now):
        if self.t0 is None:
            self.t0 = now - (self.first or 0.0)

    def after_request(self, now, weight, unit, request_meta_data):
        pass

    def next(self, current):
        if self.index is None:
            self.index = self._client_index()
        now = self._now(current)
        if self.unit == "qps":
            nxt = self._next_qps(current, now)
        else:
            nxt = self._next_clients(current, now)
        if self.first is None:
            self.first = nxt
        return nxt

    # ---- shape time ---------------------------------------------------------------------------------------

    def _now(self, current):
        """Seconds since the task's time 0: the clock once known, else the last scheduled slot."""
        return time.perf_counter() - self.t0 if self.t0 is not None else current

    def _level(self, t):
        return load_shape.level(self.shape, t - self.warmup) if t < self.end else 0.0

    def _rate(self, t):
        """This client's target rate (requests/s) at task time ``t``."""
        return self.max * self._level(t) / self.clients

    def _active(self, t):
        return self.index < round(self.max * self._level(t))

    def _next_when(self, t, test):
        """The first task time >= t where test(t) holds, before the shape's end, else None."""
        while t < self.end:
            if test(t):
                return t
            t += SCAN_S
        return None

    # ---- modes --------------------------------------------------------------------------------------------

    def _next_qps(self, current, now):
        if self.first is None:
            t = self._next_when(0.0, lambda x: self._rate(x) > FLOOR_QPS)
            if t is None:
                self._stop("shape has no load")
            # spread the clients over the first interval so they don't fire in lockstep
            return t + random.uniform(0, 1.0 / self._rate(t))
        rate = self._rate(current)
        if rate <= FLOOR_QPS:
            t = self._next_when(current, lambda x: self._rate(x) > FLOOR_QPS)
            if t is None:
                self._stop("shape ended")
            return t
        nxt = current + 1.0 / rate
        skipped = 0
        if nxt < now - 1.0 / rate:          # more than one interval late: skip the missed slots
            skipped = int((now - nxt) * rate)
            nxt = now
        if self._rate(nxt) <= FLOOR_QPS:      # the slot falls in an "off" stretch: wait for the load to return
            nxt = self._next_when(nxt, lambda x: self._rate(x) > FLOOR_QPS)
            if nxt is None:
                self._stop("shape ended")
        if nxt >= self.end:
            self._stop("shape ended")
        self._count(nxt, skipped)
        return nxt

    def _next_clients(self, current, now):
        t = max(current, now)
        if not self._active(t):
            t = self._next_when(t, self._active)
            if t is None:
                self._stop("shape ended")
        elif t >= self.end:
            self._stop("shape ended")
        self._count(t, 0)
        return t

    # ---- bookkeeping --------------------------------------------------------------------------------------

    def _count(self, t, skipped):
        self.slots += 1
        self.skipped += skipped
        if t - self.last_progress >= 60:
            self.last_progress = t
            self._log("SHAPE_PROGRESS", t)
        if self.unit != "qps" or t < self.warmup:
            return
        self.recent.append((t, 1, skipped))
        while self.recent and self.recent[0][0] < t - self.limit_window:
            self.recent.popleft()
        if not self.stop_when_limited or t - self.warmup < self.limit_window:
            return
        n = sum(s for _, s, _ in self.recent)
        k = sum(k for _, _, k in self.recent)
        if k / (n + k) > self.limit_fraction:
            target = self.max * self._level(t)
            # this client's sent rate over the window, times the clients: the task-wide rate (clients share the target evenly)
            achieved = self.clients * n / max(t - self.recent[0][0], 1e-9)
            self.logger.warning("SHAPE_CLIENT_LIMITED at=%.0f target=%.1f achieved=%.1f clients=%d task=%s",
                                t - self.warmup, target, achieved, self.clients, self.task)
            self._stop("client limited")

    def _stop(self, why):
        if not self.stopped:
            self.stopped = True
            self._log("SHAPE_END", None, why)
        raise StopIteration(why)

    def _log(self, what, t, why=None):
        self.logger.info("%s task=%s client=%s t=%s slots=%d skipped=%d%s", what, self.task, self.index,
                         "-" if t is None else int(t - self.warmup), self.slots, self.skipped,
                         f" reason={why}" if why else "")

    def _client_index(self):
        """This client's index in the task, for the client modes. OSB doesn't hand it to schedulers, but the
        corpus-sample parameter source keeps the partition index it was given. Without one, a random index
        keeps the active count right on average."""
        index = getattr(self.parameter_source, "partition_index", None)
        if isinstance(index, int) and 0 <= index < self.clients:
            return index
        if self.unit == "clients":
            self.logger.warning("shape scheduler: no client index from the parameter source; using a random one")
        return random.randrange(self.clients)

    def __str__(self):
        return f"shape scheduler ({self.shape['type']}, {self.unit}, max {self.max:g})"
