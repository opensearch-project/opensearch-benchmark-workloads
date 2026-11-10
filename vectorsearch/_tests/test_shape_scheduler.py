# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Load shapes and the shape scheduler, driven the way OSB's executor drives a scheduler, on a fake clock.

Run from the repository root: python -m unittest vectorsearch._tests.test_shape_scheduler (in _tests so OSB, which imports every module of a workload, skips it)
"""
import math
import re
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from vectorsearch import load_shape, shape_scheduler
from vectorsearch.shape_scheduler import ShapeScheduler


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def task(shape, clients, warmup=None):
    return SimpleNamespace(params={"shape": shape}, clients=clients, warmup_time_period=warmup,
                           __str__=lambda self: "t")


def run_client(shape, clients, index, latency, warmup=None):
    """One client as OSB runs it: next() -> sleep until the slot (or not, if late) -> before_request ->
    request (latency(t) s) -> next(previous slot). Returns ([request start times, task-relative], stop reason)."""
    clock = Clock()
    s = ShapeScheduler(task(shape, clients, warmup))
    s.parameter_source = SimpleNamespace(partition_index=index)
    total_start, starts, current = clock.now, [], 0.0
    with mock.patch.object(shape_scheduler.time, "perf_counter", clock):
        try:
            while True:
                current = s.next(current)
                clock.now = max(clock.now, total_start + current)
                s.before_request(clock.now)
                starts.append(clock.now - total_start)
                clock.now += latency(clock.now - total_start)
        except StopIteration as e:
            return starts, str(e)


def per_phase(starts_by_client, shape, warmup=0.0):
    out = []
    for name, a, b, lv in load_shape.phases(shape):
        n = sum(1 for starts in starts_by_client for t in starts if a <= t - warmup < b)
        out.append((name, lv, n / (b - a)))
    return out


class Shapes(unittest.TestCase):
    def test_levels_and_durations(self):
        steps = load_shape.parse({"type": "steps", "max": 100, "levels": [{"level": 0.2, "s": 60}, {"level": 1, "s": 30}]})
        self.assertEqual(load_shape.duration(steps), 90)
        self.assertEqual((load_shape.level(steps, 10), load_shape.level(steps, 70), load_shape.level(steps, 95)),
                         (0.2, 1.0, 0.0))
        ramp = load_shape.parse({"type": "ramp", "max": 100, "from": 0, "to": 1, "upS": 100, "holdS": 50, "downS": 100})
        self.assertAlmostEqual(load_shape.level(ramp, 50), 0.5)
        self.assertEqual(load_shape.level(ramp, 120), 1.0)
        self.assertAlmostEqual(load_shape.level(ramp, 200), 0.5)
        burst = load_shape.parse({"type": "burst", "max": 100, "low": 0.1, "high": 1, "onS": 10, "offS": 20, "cycles": 2})
        self.assertEqual(load_shape.duration(burst), 60)
        self.assertEqual([load_shape.level(burst, t) for t in (5, 25, 35, 55)], [0.1, 1.0, 0.1, 1.0])
        sine = load_shape.parse({"type": "sine", "max": 100, "low": 0.2, "high": 1, "periodS": 100, "cycles": 2})
        self.assertAlmostEqual(load_shape.level(sine, 0), 0.2)
        self.assertAlmostEqual(load_shape.level(sine, 50), 1.0)
        self.assertAlmostEqual(load_shape.level(sine, 150), 1.0)

    def test_phases(self):
        burst = load_shape.parse({"type": "burst", "max": 1, "low": 0, "high": 1, "onS": 10, "offS": 20, "cycles": 2})
        self.assertEqual([p[0] for p in load_shape.phases(burst)], ["off-1", "on-1", "off-2", "on-2"])
        sine = load_shape.parse({"type": "sine", "max": 1, "low": 0, "high": 1, "periodS": 120})
        ph = load_shape.phases(sine)
        self.assertEqual((len(ph), ph[0][1], ph[-1][2]), (4, 0, 120))
        self.assertLess(ph[0][3], ph[1][3])

    def test_bad_shapes(self):
        for bad in ({"type": "zigzag"}, {"type": "sine", "low": 0, "high": 1, "periodS": 60},          # qps needs max
                    {"type": "sine", "max": 10, "low": 0, "high": 2, "periodS": 60},
                    {"type": "steps", "max": 10, "levels": []}, {"type": "ramp", "unit": "x", "max": 1},
                    "not json"):
            with self.assertRaises(load_shape.ShapeError, msg=bad):
                load_shape.parse(bad)
        self.assertEqual(load_shape.parse({"type": "burst", "unit": "clients", "low": 0, "high": 1, "onS": 1,
                                           "offS": 1})["unit"], "clients")


class QpsMode(unittest.TestCase):
    STEPS = {"type": "steps", "unit": "qps", "max": 200,
             "levels": [{"level": 0.25, "s": 60}, {"level": 1.0, "s": 60}, {"level": 0.5, "s": 60}]}

    def test_follows_the_target_per_phase(self):
        random.seed(1)
        runs = [run_client(self.STEPS, 8, i, lambda t: 0.01) for i in range(8)]
        self.assertTrue(all(r[1] == "shape ended" for r in runs))
        for name, lv, qps in per_phase([r[0] for r in runs], load_shape.parse(self.STEPS)):
            self.assertAlmostEqual(qps, 200 * lv, delta=0.05 * 200 * lv, msg=name)

    def test_no_catch_up_after_a_slow_peak(self):
        # latency 0.5 s during 60-80 s: 8 clients can do 16 qps against a 200 qps target. After it, the
        # trough must run at its own target, not burst to make up the missed requests.
        random.seed(2)
        shape = dict(self.STEPS, stopWhenLimited=False)
        slow = lambda t: 0.5 if 60 <= t < 80 else 0.01                      # noqa: E731
        runs = [run_client(shape, 8, i, slow) for i in range(8)]
        after = sum(1 for r in runs for t in r[0] if 125 <= t < 180) / 55
        self.assertAlmostEqual(after, 100, delta=5)

    def test_client_limited_ends_the_task(self):
        shape = {"type": "ramp", "unit": "qps", "max": 400, "from": 0.1, "to": 1, "upS": 300}
        # 4 clients at 0.05 s can do 80 qps: limited once the ramp passes ~80 / (1 - 0.1)
        with self.assertLogs(shape_scheduler.__name__, "WARNING") as log:
            starts, why = run_client(shape, 4, 0, lambda t: 0.05)
        self.assertEqual(why, "client limited")
        self.assertIn("SHAPE_CLIENT_LIMITED", "\n".join(log.output))
        self.assertLess(starts[-1], 150)
        achieved = float(re.search(r"achieved=([\d.]+)", "\n".join(log.output)).group(1))
        self.assertTrue(60 < achieved <= 84, achieved)                     # at most 4 clients x 1 / 0.05 s

    def test_burst_with_zero_low_waits_for_the_next_on(self):
        shape = {"type": "burst", "unit": "qps", "max": 50, "low": 0, "high": 1, "onS": 10, "offS": 20, "cycles": 2}
        starts, why = run_client(shape, 1, 0, lambda t: 0.001)
        self.assertEqual(why, "shape ended")
        self.assertFalse([t for t in starts if t < 20 or 30 <= t < 50])
        self.assertAlmostEqual(sum(1 for t in starts if 20 <= t < 30) / 10, 50, delta=3)

    def test_warmup_runs_at_the_starting_level(self):
        shape = {"type": "steps", "unit": "qps", "max": 100, "levels": [{"level": 0.5, "s": 30}]}
        starts, _ = run_client(shape, 1, 0, lambda t: 0.001, warmup=20)
        self.assertAlmostEqual(sum(1 for t in starts if t < 20) / 20, 50, delta=3)
        self.assertLess(starts[-1], 50)


class ClientMode(unittest.TestCase):
    def active_over_time(self, shape, clients, mx_clients=None):
        runs = [run_client(shape, clients, i, lambda t: 0.1) for i in range(clients)]
        return lambda t: sum(1 for starts, _ in runs if any(t <= s < t + 0.2 for s in starts))

    def test_active_clients_follow_the_shape(self):
        shape = {"type": "steps", "unit": "clients", "max": 8,
                 "levels": [{"level": 0.25, "s": 20}, {"level": 1, "s": 20}, {"level": 0.5, "s": 20}]}
        active = self.active_over_time(shape, 8)
        self.assertEqual([active(t) for t in (10, 30, 50)], [2, 8, 4])

    def test_no_max_uses_every_client_and_max_is_capped(self):
        shape = {"type": "burst", "unit": "clients", "low": 0.25, "high": 1, "onS": 10, "offS": 10}
        active = self.active_over_time(shape, 4)
        self.assertEqual([active(t) for t in (5, 15)], [1, 4])
        s = ShapeScheduler(task(dict(shape, max=99), 4))
        self.assertEqual(s.max, 4)

    def test_full_speed_while_active(self):
        shape = {"type": "steps", "unit": "clients", "max": 1, "levels": [{"level": 1, "s": 10}]}
        starts, why = run_client(shape, 1, 0, lambda t: 0.1)
        self.assertEqual((why, len(starts)), ("shape ended", 100))


class Registration(unittest.TestCase):
    def test_osb_treats_it_as_a_full_scheduler(self):
        try:
            from osbenchmark.worker_coordinator import scheduler
        except ImportError:
            self.skipTest("opensearch-benchmark not installed")
        self.assertFalse(scheduler.is_simple_scheduler(ShapeScheduler))
        self.assertFalse(scheduler.is_legacy_scheduler(ShapeScheduler))
        self.assertTrue(hasattr(ShapeScheduler(task({"type": "sine", "max": 1, "low": 0, "high": 1,
                                                     "periodS": 1}, 1)), "parameter_source"))


if __name__ == "__main__":
    unittest.main()
