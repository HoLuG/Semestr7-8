"""Deterministic world positions (shared by simulation init and optional fallbacks)."""
from __future__ import annotations

import math
from typing import Tuple

from sim.model import BlackHole, BodyKind, CelestialBody, Universe

TWO_PI = 2 * math.pi


def _hash01(n: int) -> float:
    x = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (x % 10000) / 10000.0


# Alias for viewers / tools outside sim.
hash01 = _hash01


def _stable_angle(seed: int) -> float:
    return (seed * 0.618033988749895) % TWO_PI


def sector_scale(u: Universe) -> float:
    return 400.0 * (0.6 + u.scale) ** 0.45


def star_layout_xy(star: CelestialBody, u: Universe) -> Tuple[float, float]:
    S = sector_scale(u)
    arm = star.id % 11
    hub_ang = arm * 0.573
    hub_r = S * (0.15 + 0.55 * _hash01(star.id + 7))
    hx = hub_r * math.cos(hub_ang)
    hy = hub_r * math.sin(hub_ang)
    local_ang = TWO_PI * _hash01(star.id * 9973)
    local_r = S * (0.04 + 0.35 * math.sqrt(_hash01(star.id + 101)))
    lx = local_r * math.cos(local_ang)
    ly = local_r * math.sin(local_ang)
    r = math.hypot(hx + lx, hy + ly)
    twist = 0.25 * math.sin(r * 0.008 + star.id * 0.01)
    ca, sa = math.cos(twist), math.sin(twist)
    wx = (hx + lx) * ca - (hy + ly) * sa
    wy = (hx + lx) * sa + (hy + ly) * ca
    return wx, wy


def black_hole_layout_xy(bh: BlackHole, u: Universe) -> Tuple[float, float]:
    """Id-based shell (stable when the hole list is reordered)."""
    S = sector_scale(u)
    ring = S * (1.05 + 0.35 * _hash01(bh.id + 3))
    ang = TWO_PI * _hash01(bh.id * 997) + _stable_angle(bh.id * 31)
    wobble = 0.12 * math.sin(bh.id * 0.07)
    return ring * math.cos(ang + wobble), ring * math.sin(ang + wobble)


def nebula_layout_xy(neb: CelestialBody, u: Universe) -> Tuple[float, float]:
    S = sector_scale(u)
    na = _stable_angle(neb.id + 1000)
    nr = S * (0.35 + 0.4 * _hash01(neb.id))
    return nr * math.cos(na), nr * math.sin(na)


def exotic_layout_xy(ex: CelestialBody, u: Universe) -> Tuple[float, float]:
    S = sector_scale(u)
    ea = _stable_angle(ex.id + 3333)
    er = S * (0.5 + 0.45 * _hash01(ex.id + 50))
    return er * math.cos(ea), er * math.sin(ea)


def planet_orbit_radius(pl: CelestialBody, u: Universe) -> float:
    S = sector_scale(u)
    return 28.0 + pl.distance_band * S * 0.24
