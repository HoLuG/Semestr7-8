"""Gravity, Kepler-like orbits, and horizon absorption (same world space as viz)."""
from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

from sim.layout import (
    TWO_PI,
    _stable_angle,
    black_hole_layout_xy,
    exotic_layout_xy,
    nebula_layout_xy,
    planet_orbit_radius,
    sector_scale,
    star_layout_xy,
)
from sim.model import (
    BlackHole,
    BodyKind,
    CelestialBody,
    Multiverse,
    Universe,
    body_information_value,
)

def _moon_host_planet(u: Universe, moon: CelestialBody) -> Optional[CelestialBody]:
    if moon.host_planet_id is not None:
        for p in u.bodies:
            if p.id == moon.host_planet_id and p.kind == BodyKind.PLANET:
                return p
    candidates = [
        p
        for p in u.bodies
        if p.kind == BodyKind.PLANET
        and (moon.host_star_id is None or p.host_star_id == moon.host_star_id)
    ]
    return candidates[0] if candidates else None


def _snapshot_render_prev(u: Universe) -> None:
    for bh in u.black_holes:
        bh.render_prev_x, bh.render_prev_y = bh.pos_x, bh.pos_y
    for b in u.bodies:
        if b.kind in (
            BodyKind.STAR,
            BodyKind.PLANET,
            BodyKind.MOON,
            BodyKind.NEBULA,
            BodyKind.EXOTIC,
        ):
            b.render_prev_x, b.render_prev_y = b.pos_x, b.pos_y


def _clamp_speed(vx: float, vy: float, vmax: float) -> Tuple[float, float]:
    v = math.hypot(vx, vy)
    if v > vmax > 1e-9:
        s = vmax / v
        return vx * s, vy * s
    return vx, vy


def _enforce_sphere_and_bounce(
    px: float, py: float, vx: float, vy: float, lim: float, inward_boost: float
) -> Tuple[float, float, float, float]:
    r = math.hypot(px, py)
    if r > lim and r > 1e-9:
        px, py = px * lim / r, py * lim / r
        nx, ny = px / max(lim, 1e-9), py / max(lim, 1e-9)
        vr = vx * nx + vy * ny
        if vr > 0:
            vx -= (1.0 + inward_boost) * vr * nx
            vy -= (1.0 + inward_boost) * vr * ny
    return px, py, vx, vy


def _strip_nebula_near_black_holes(m: Multiverse, u: Universe, cfg: Any) -> None:
    """Gradual mass loss for nebulae near BHs (accretion), without full swallow."""
    if not u.black_holes:
        return
    for bh in u.black_holes:
        r_acc = cfg.nebula_accretion_radius_factor * math.sqrt(max(0.08, bh.mass))
        for neb in list(u.bodies):
            if neb.kind != BodyKind.NEBULA:
                continue
            d = math.hypot(neb.pos_x - bh.pos_x, neb.pos_y - bh.pos_y)
            if d >= r_acc:
                continue
            w = 1.0 - d / max(r_acc, 1e-6)
            loss = cfg.nebula_mass_loss_per_tick * w * (0.65 + 0.35 * min(3.0, bh.mass))
            if loss <= 0:
                continue
            neb.mass_index -= loss
            bh.information_swallowed += loss * 0.45
            bh.mass = max(0.08, bh.mass + loss * 0.06)
            if neb.mass_index <= cfg.nebula_min_mass:
                u.bodies.remove(neb)
                m.bodies.pop(neb.id, None)


def initialize_universe_positions(m: Multiverse, u: Universe) -> None:
    """Assign layout positions to any object not yet placed."""
    stars = [b for b in u.bodies if b.kind == BodyKind.STAR]
    for s in stars:
        if not s.spatial_ready:
            s.pos_x, s.pos_y = star_layout_xy(s, u)
            s.vel_x = s.vel_y = 0.0
            s.render_prev_x, s.render_prev_y = s.pos_x, s.pos_y
            s.spatial_ready = True

    for bh in u.black_holes:
        if not bh.spatial_ready:
            bh.pos_x, bh.pos_y = black_hole_layout_xy(bh, u)
            bh.vel_x = bh.vel_y = 0.0
            bh.render_prev_x, bh.render_prev_y = bh.pos_x, bh.pos_y
            bh.spatial_ready = True

    for b in u.bodies:
        if b.kind == BodyKind.NEBULA and not b.spatial_ready:
            b.pos_x, b.pos_y = nebula_layout_xy(b, u)
            b.vel_x = b.vel_y = 0.0
            b.render_prev_x, b.render_prev_y = b.pos_x, b.pos_y
            b.spatial_ready = True
        elif b.kind == BodyKind.EXOTIC and not b.spatial_ready:
            b.pos_x, b.pos_y = exotic_layout_xy(b, u)
            b.vel_x = b.vel_y = 0.0
            b.render_prev_x, b.render_prev_y = b.pos_x, b.pos_y
            b.spatial_ready = True

    star_map = {s.id: s for s in stars}
    for pl in u.bodies:
        if pl.kind != BodyKind.PLANET:
            continue
        st = star_map.get(pl.host_star_id) if pl.host_star_id is not None else None
        if not pl.spatial_ready:
            pl.orbit_angle = _stable_angle(pl.id * 7919)
            pl.spatial_ready = True
        if st is None:
            continue
        r = planet_orbit_radius(pl, u)
        pl.pos_x = st.pos_x + math.cos(pl.orbit_angle) * r
        pl.pos_y = st.pos_y + math.sin(pl.orbit_angle) * r

    for moon in u.bodies:
        if moon.kind != BodyKind.MOON:
            continue
        pl = _moon_host_planet(u, moon)
        if pl is None:
            continue
        if not moon.spatial_ready:
            moon.moon_orbit_angle = _stable_angle(moon.id) + 0.5
            moon.spatial_ready = True
        moon_r = 22.0
        moon.pos_x = pl.pos_x + math.cos(moon.moon_orbit_angle) * moon_r
        moon.pos_y = pl.pos_y + math.sin(moon.moon_orbit_angle) * moon_r


def _bh_acceleration(
    bh: BlackHole, holes: List[BlackHole], G: float, soft2: float
) -> Tuple[float, float]:
    ax, ay = 0.0, 0.0
    for o in holes:
        if o is bh:
            continue
        dx = o.pos_x - bh.pos_x
        dy = o.pos_y - bh.pos_y
        dist2 = dx * dx + dy * dy + soft2
        inv = dist2 ** (-1.5)
        ax += G * o.mass * dx * inv
        ay += G * o.mass * dy * inv
    return ax, ay


def _accel_from_black_holes(
    px: float, py: float, holes: List[BlackHole], G: float, soft2: float
) -> Tuple[float, float]:
    """Acceleration of a test mass from Newtonian gravity (softened)."""
    ax, ay = 0.0, 0.0
    for bh in holes:
        dx = bh.pos_x - px
        dy = bh.pos_y - py
        dist2 = dx * dx + dy * dy + soft2
        inv = dist2 ** (-1.5)
        ax += G * bh.mass * dx * inv
        ay += G * bh.mass * dy * inv
    return ax, ay


def _gain_mass_from_body(b: CelestialBody) -> float:
    if b.kind == BodyKind.STAR:
        return b.mass_index * 0.32
    if b.kind == BodyKind.PLANET:
        return b.mass_index * 0.48
    if b.kind == BodyKind.MOON:
        return b.mass_index * 0.35
    if b.kind == BodyKind.NEBULA:
        return b.mass_index * 0.42
    return b.mass_index * 0.45


def step_dynamics(m: Multiverse, u: Universe, cfg: Any) -> None:
    initialize_universe_positions(m, u)
    _snapshot_render_prev(u)
    dt = cfg.dynamics_dt
    soft2 = cfg.gravity_softening ** 2
    soft2_bb = cfg.gravity_softening_bh_bh ** 2
    Gsb = cfg.grav_star_bh * u.physics.gravity_coupling
    Gbb = cfg.grav_bh_bh * u.physics.gravity_coupling
    lim = sector_scale(u) * cfg.universe_radius_scale
    holes = u.black_holes

    # --- Black holes: mutual gravity + weak wander ---
    bh_acc: List[Tuple[float, float]] = []
    for bh in holes:
        ax, ay = _bh_acceleration(bh, holes, Gbb, soft2_bb)
        ax += cfg.bh_wander_accel * m.rng.gauss(0.0, 1.0)
        ay += cfg.bh_wander_accel * m.rng.gauss(0.0, 1.0)
        bh_acc.append((ax, ay))
    for bh, (ax, ay) in zip(holes, bh_acc):
        bh.vel_x = (bh.vel_x + ax * dt) * cfg.bh_velocity_damping
        bh.vel_y = (bh.vel_y + ay * dt) * cfg.bh_velocity_damping
        bh.vel_x, bh.vel_y = _clamp_speed(bh.vel_x, bh.vel_y, cfg.max_bh_speed)
        bh.pos_x += bh.vel_x * dt
        bh.pos_y += bh.vel_y * dt
        bh.pos_x, bh.pos_y, bh.vel_x, bh.vel_y = _enforce_sphere_and_bounce(
            bh.pos_x, bh.pos_y, bh.vel_x, bh.vel_y, lim, cfg.boundary_bounce_strength
        )

    # --- Free bodies pulled by black holes ---
    for b in u.bodies:
        if b.kind not in (BodyKind.STAR, BodyKind.NEBULA, BodyKind.EXOTIC):
            continue
        ax, ay = _accel_from_black_holes(b.pos_x, b.pos_y, holes, Gsb, soft2)
        damp = cfg.star_velocity_damping
        b.vel_x = (b.vel_x + ax * dt) * damp
        b.vel_y = (b.vel_y + ay * dt) * damp
        b.vel_x, b.vel_y = _clamp_speed(b.vel_x, b.vel_y, cfg.max_free_body_speed)
        b.pos_x += b.vel_x * dt
        b.pos_y += b.vel_y * dt
        b.pos_x, b.pos_y, b.vel_x, b.vel_y = _enforce_sphere_and_bounce(
            b.pos_x, b.pos_y, b.vel_x, b.vel_y, lim, cfg.boundary_bounce_strength
        )

    # --- Planets on orbits around host stars (stars already moved) ---
    stars = [s for s in u.bodies if s.kind == BodyKind.STAR]
    star_map = {s.id: s for s in stars}
    for pl in u.bodies:
        if pl.kind != BodyKind.PLANET:
            continue
        st = star_map.get(pl.host_star_id) if pl.host_star_id is not None else None
        if st is None:
            continue
        r = max(8.0, planet_orbit_radius(pl, u))
        omega = cfg.orbit_omega_scale * math.sqrt(max(0.15, st.mass_index)) / (r**0.62)
        pl.orbit_angle = (pl.orbit_angle + omega * dt) % TWO_PI
        pl.pos_x = st.pos_x + math.cos(pl.orbit_angle) * r
        pl.pos_y = st.pos_y + math.sin(pl.orbit_angle) * r

    # --- Moons around planets ---
    moon_r = 22.0
    for moon in u.bodies:
        if moon.kind != BodyKind.MOON:
            continue
        pl = _moon_host_planet(u, moon)
        if pl is None:
            continue
        omega_m = cfg.moon_orbit_omega_scale / max(6.0, moon_r**0.55)
        moon.moon_orbit_angle = (moon.moon_orbit_angle + omega_m * dt) % TWO_PI
        moon.pos_x = pl.pos_x + math.cos(moon.moon_orbit_angle) * moon_r
        moon.pos_y = pl.pos_y + math.sin(moon.moon_orbit_angle) * moon_r

    _strip_nebula_near_black_holes(m, u, cfg)
    # --- Swallow matter inside effective horizons ---
    _absorb_at_horizons(m, u, cfg)


def _absorb_at_horizons(m: Multiverse, u: Universe, cfg: Any) -> None:
    if not u.black_holes:
        return
    n_stars = sum(1 for b in u.bodies if b.kind == BodyKind.STAR)

    def try_swallow(b: CelestialBody) -> bool:
        nonlocal n_stars
        if b.kind == BodyKind.STAR and n_stars <= 1:
            if m.rng.random() < cfg.absorb_spare_last_star_p:
                return False
        best_bh: BlackHole | None = None
        best_ratio = 1e9
        for bh in u.black_holes:
            rs = cfg.absorb_radius_factor * math.sqrt(max(0.06, bh.mass))
            if b.kind == BodyKind.NEBULA:
                rs *= cfg.nebula_swallow_radius_mult
            d = math.hypot(b.pos_x - bh.pos_x, b.pos_y - bh.pos_y)
            if d < rs:
                ratio = d / max(rs, 1e-6)
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_bh = bh
        if best_bh is None:
            return False
        info = body_information_value(b)
        best_bh.information_swallowed += info
        best_bh.mass = max(0.08, best_bh.mass + _gain_mass_from_body(b))
        if b.kind == BodyKind.PLANET:
            for orphan in list(u.bodies):
                if orphan.kind == BodyKind.MOON and orphan.host_planet_id == b.id:
                    u.bodies.remove(orphan)
                    m.bodies.pop(orphan.id, None)
        if b.kind == BodyKind.STAR:
            n_stars -= 1
            for orphan in list(u.bodies):
                if orphan.kind == BodyKind.PLANET and orphan.host_star_id == b.id:
                    u.bodies.remove(orphan)
                    m.bodies.pop(orphan.id, None)
                if orphan.kind == BodyKind.MOON and orphan.host_star_id == b.id:
                    u.bodies.remove(orphan)
                    m.bodies.pop(orphan.id, None)
        u.bodies.remove(b)
        m.bodies.pop(b.id, None)
        return True

    changed = True
    while changed:
        changed = False
        for b in list(u.bodies):
            if b.kind not in (
                BodyKind.STAR,
                BodyKind.PLANET,
                BodyKind.MOON,
                BodyKind.NEBULA,
                BodyKind.EXOTIC,
            ):
                continue
            if try_swallow(b):
                changed = True
                break


def bh_pair_merge_weight(a: BlackHole, b: BlackHole, cfg: Any, u: Universe) -> float:
    """Extra probability weight from separation (close = more likely)."""
    d = math.hypot(a.pos_x - b.pos_x, a.pos_y - b.pos_y)
    prod_mass = (a.mass * b.mass) ** 0.5
    d0 = cfg.merge_contact_distance * (prod_mass**0.42 + 0.12)
    # Strong pull when overlapping "contact" disk
    if d < d0 * 0.85:
        return 2.8 + 1.4 * (1.0 - d / max(d0, 1e-6))
    span = sector_scale(u) * 0.45
    prox = math.exp(-max(0.0, d - d0) / max(span, 1e-6))
    return 0.35 + 0.95 * prox
