# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Load shapes for one continuous OSB task: steps, ramp, burst and sine.

A shape is a dict. Its level is a fraction of the shape's ``max`` (0..1) at each second ``t`` from the
shape's start, so one shape works in either unit:

* ``unit: "qps"``: ``max`` is the peak request rate (required); the level times ``max`` is the target rate.
* ``unit: "clients"``: ``max`` is the peak number of active clients (default: the task's clients); the
  level times ``max``, rounded, is how many clients send at full speed at ``t``.

Shapes (all durations in seconds, levels in 0..1)::

    {"type": "steps", "levels": [{"level": 0.2, "s": 600}, {"level": 1.0, "s": 600}]}
    {"type": "ramp",  "from": 0.1, "to": 1.0, "upS": 1800, "holdS": 600, "downS": 1800}
    {"type": "burst", "low": 0.1, "high": 1.0, "onS": 120, "offS": 600, "cycles": 4}
    {"type": "sine",  "low": 0.1, "high": 1.0, "periodS": 1800, "cycles": 3}

A burst starts with its "off" (low) phase; a sine starts at ``low`` and peaks half a period in.
Pure functions only: the scheduler and the benchmark report both use them, so the target is computed one
way everywhere.
"""
import json
import math

TYPES = ("steps", "ramp", "burst", "sine")
UNITS = ("qps", "clients")
BIN_S = 30


class ShapeError(ValueError):
    pass


def _num(shape, key, lo=None, hi=None, positive=False, default=None):
    v = shape.get(key, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ShapeError(f"shape {shape.get('type')}: {key} must be a number, got {v!r}")
    if positive and v <= 0:
        raise ShapeError(f"shape {shape.get('type')}: {key} must be > 0, got {v}")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise ShapeError(f"shape {shape.get('type')}: {key} must be in [{lo}, {hi}], got {v}")
    return v


def parse(shape):
    """The shape as a validated dict (a JSON string is accepted too). Raises ShapeError."""
    if isinstance(shape, str):
        try:
            shape = json.loads(shape)
        except ValueError as e:
            raise ShapeError(f"shape is not JSON: {e}") from None
    if not isinstance(shape, dict):
        raise ShapeError(f"shape must be an object, got {type(shape).__name__}")
    t = shape.get("type")
    if t not in TYPES:
        raise ShapeError(f"shape type must be one of {', '.join(TYPES)}, got {t!r}")
    unit = shape.get("unit", "qps")
    if unit not in UNITS:
        raise ShapeError(f"shape unit must be one of {', '.join(UNITS)}, got {unit!r}")
    if unit == "qps":
        _num(shape, "max", positive=True)
    elif shape.get("max") is not None:
        _num(shape, "max", positive=True)
    if t == "steps":
        levels = shape.get("levels")
        if not isinstance(levels, list) or not levels:
            raise ShapeError("shape steps: levels must be a non-empty list")
        for i, lv in enumerate(levels):
            if not isinstance(lv, dict):
                raise ShapeError(f"shape steps: level {i} must be an object")
            _num(dict(lv, type="steps"), "level", 0, 1)
            _num(dict(lv, type="steps"), "s", positive=True)
    elif t == "ramp":
        for k in ("from", "to"):
            _num(shape, k, 0, 1)
        _num(shape, "upS", positive=True)
        for k in ("holdS", "downS"):
            _num(shape, k, lo=0, default=0)
    elif t == "burst":
        for k in ("low", "high"):
            _num(shape, k, 0, 1)
        for k in ("onS", "offS"):
            _num(shape, k, positive=True)
        _num(shape, "cycles", positive=True, default=1)
    else:
        for k in ("low", "high"):
            _num(shape, k, 0, 1)
        _num(shape, "periodS", positive=True)
        _num(shape, "cycles", positive=True, default=1)
    return dict(shape, unit=unit)


def duration(shape):
    """Seconds the shape lasts."""
    t = shape["type"]
    if t == "steps":
        return float(sum(lv["s"] for lv in shape["levels"]))
    if t == "ramp":
        return float(shape["upS"] + shape.get("holdS", 0) + shape.get("downS", 0))
    if t == "burst":
        return float((shape["onS"] + shape["offS"]) * shape.get("cycles", 1))
    return float(shape["periodS"] * shape.get("cycles", 1))


def level(shape, t):
    """The level (0..1) at ``t`` seconds from the shape's start; 0 after the end."""
    if t < 0:
        t = 0.0
    if t >= duration(shape):
        return 0.0
    kind = shape["type"]
    if kind == "steps":
        edge = 0.0
        for lv in shape["levels"]:
            edge += lv["s"]
            if t < edge:
                return float(lv["level"])
        return 0.0
    if kind == "ramp":
        lo, hi, up, hold = shape["from"], shape["to"], shape["upS"], shape.get("holdS", 0)
        if t < up:
            return lo + (hi - lo) * t / up
        if t < up + hold:
            return float(hi)
        down = shape.get("downS", 0)
        return hi + (lo - hi) * (t - up - hold) / down
    if kind == "burst":
        cycle = shape["onS"] + shape["offS"]
        return float(shape["low"] if (t % cycle) < shape["offS"] else shape["high"])
    lo, hi, p = shape["low"], shape["high"], shape["periodS"]
    return lo + (hi - lo) * (1 - math.cos(2 * math.pi * t / p)) / 2


def phases(shape, bin_s=BIN_S):
    """[(name, start_s, end_s, mean_level)]: each step or burst phase, or ``bin_s`` bins for ramp and sine,
    so results can be cut per phase against the target."""
    kind, out = shape["type"], []
    if kind == "steps":
        edge = 0.0
        for i, lv in enumerate(shape["levels"]):
            out.append((f"step-{i + 1}", edge, edge + lv["s"], float(lv["level"])))
            edge += lv["s"]
        return out
    if kind == "burst":
        edge = 0.0
        for c in range(int(math.ceil(shape.get("cycles", 1)))):
            for name, s, lv in (("off", shape["offS"], shape["low"]), ("on", shape["onS"], shape["high"])):
                end = min(edge + s, duration(shape))
                if end > edge:
                    out.append((f"{name}-{c + 1}", edge, end, float(lv)))
                edge += s
        return out
    total, t = duration(shape), 0.0
    while t < total:
        end = min(t + bin_s, total)
        n = 20
        mean = sum(level(shape, t + (end - t) * (i + 0.5) / n) for i in range(n)) / n
        out.append((f"t{int(t)}", t, end, mean))
        t = end
    return out
