"""
Procedural sprite cache for celestial bodies (no external image files).
"""
from __future__ import annotations

import math
from typing import Dict, Tuple

import pygame

TWO_PI = math.pi * 2

# (kind_key, body_id, size_bucket, color_key) -> Surface
_CACHE: Dict[Tuple[str, int, int, int], pygame.Surface] = {}
_MAX_CACHE = 256


def _fbm01(x: float, y: float, seed: int) -> float:
    v = 0.0
    a = 0.5
    f = 1.0
    for _ in range(4):
        vx = math.sin(f * x * 3.1 + seed * 0.017)
        vy = math.cos(f * y * 2.7 + seed * 0.023)
        v += a * (vx * vy * 0.5 + 0.5)
        f *= 2.0
        a *= 0.5
    return max(0.0, min(1.0, v))


def _cache_put(key: Tuple[str, int, int, int], surf: pygame.Surface) -> pygame.Surface:
    if len(_CACHE) > _MAX_CACHE:
        for _ in range(_MAX_CACHE // 4):
            try:
                _CACHE.pop(next(iter(_CACHE)))
            except StopIteration:
                break
    _CACHE[key] = surf
    return surf


def star_sprite(diameter: int, body_id: int, rgb: Tuple[int, int, int]) -> pygame.Surface:
    d = max(8, min(96, diameter))
    ck = (rgb[0] >> 3) + (rgb[1] >> 3) * 32 + (rgb[2] >> 3) * 1024
    key = ("star", body_id, d, ck)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = (d - 1) * 0.5
    cy = (d - 1) * 0.5
    r = d * 0.48
    r2 = r * r
    cr, cg, cb = rgb
    for y in range(d):
        for x in range(d):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy > r2:
                continue
            t = math.sqrt(dx * dx + dy * dy) / max(0.001, r)
            corona = max(0.0, 1.0 - t)
            core = corona**1.4
            rr = int(min(255, cr * (0.55 + 0.45 * core) + 40 * corona))
            gg = int(min(255, cg * (0.55 + 0.45 * core) + 35 * corona))
            bb = int(min(255, cb * (0.55 + 0.45 * core) + 25 * corona))
            surf.set_at((x, y), (rr, gg, bb, 255))
    pygame.draw.circle(surf, (255, 255, 255, 90), (int(cx), int(cy)), max(1, d // 8))
    return _cache_put(key, surf)


def planet_sprite(diameter: int, body_id: int, base: Tuple[int, int, int]) -> pygame.Surface:
    d = max(10, min(80, diameter))
    key = ("pl", body_id, d, base[0] + base[1] * 256 + base[2] * 65536)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = (d - 1) * 0.5
    cy = (d - 1) * 0.5
    r = d * 0.48
    r2 = r * r
    br, bg, bb = base
    for y in range(d):
        for x in range(d):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy > r2:
                continue
            nz = math.sqrt(max(0.0, r2 - dx * dx - dy * dy)) / r
            u = math.atan2(dy, dx) / TWO_PI + 0.5
            v = dy / r * 0.5 + 0.5
            n = _fbm01(u * 6 + body_id * 0.001, v * 6, body_id)
            shade = 0.35 + 0.65 * nz
            land = n * 0.35
            rr = int(max(0, min(255, br * shade * (1 - land * 0.4) + land * 30)))
            gg = int(max(0, min(255, bg * shade * (1 - land * 0.25) + land * 45)))
            bbb = int(max(0, min(255, bb * shade * (1 + land * 0.15))))
            surf.set_at((x, y), (rr, gg, bbb, 255))
    return _cache_put(key, surf)


def moon_sprite(diameter: int, body_id: int) -> pygame.Surface:
    d = max(6, min(48, diameter))
    key = ("moon", body_id, d, 0)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = (d - 1) * 0.5
    cy = (d - 1) * 0.5
    r = d * 0.48
    r2 = r * r
    for y in range(d):
        for x in range(d):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy > r2:
                continue
            nz = math.sqrt(max(0.0, r2 - dx * dx - dy * dy)) / r
            u = math.atan2(dy, dx) / TWO_PI
            n = _fbm01(u * 9, body_id * 0.01, body_id + 404)
            g = int(120 + 80 * nz + 40 * n)
            surf.set_at((x, y), (g, g, g + 8, 255))
    return _cache_put(key, surf)


def nebula_sprite(w: int, h: int, body_id: int) -> pygame.Surface:
    w = max(24, min(160, w))
    h = max(18, min(120, h))
    key = ("neb", body_id, w, h)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            n = _fbm01(x * 0.08, y * 0.08, body_id + y)
            a = int(25 + 55 * n)
            surf.set_at((x, y), (90 + int(60 * n), 120 + int(40 * n), 200, a))
    return _cache_put(key, surf)


def exotic_sprite(diameter: int, body_id: int) -> pygame.Surface:
    d = max(12, min(64, diameter))
    key = ("exo", body_id, d, 0)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = (d - 1) * 0.5
    cy = (d - 1) * 0.5
    r = d * 0.45
    r2 = r * r
    for y in range(d):
        for x in range(d):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy > r2:
                continue
            u = math.atan2(dy, dx)
            n = _fbm01(u * 3, body_id * 0.02, body_id + 900)
            rr = int(180 + 60 * n)
            gg = int(80 + 100 * (1 - n))
            bb = int(240)
            surf.set_at((x, y), (rr, gg, bb, 230))
    return _cache_put(key, surf)


def black_hole_sprite(diameter: int, body_id: int) -> pygame.Surface:
    d = max(12, min(96, diameter))
    key = ("bh", body_id, d, 0)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = (d - 1) * 0.5
    cy = (d - 1) * 0.5
    outer = d * 0.5
    for y in range(d):
        for x in range(d):
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy)
            if dist > outer:
                continue
            t = dist / outer
            if t < 0.45:
                surf.set_at((x, y), (6, 8, 14, 255))
            else:
                ring = (t - 0.45) / 0.55
                a = int(180 * (1 - ring) ** 2)
                surf.set_at((x, y), (255, 140 + int(40 * ring), 60, a))
    return _cache_put(key, surf)
