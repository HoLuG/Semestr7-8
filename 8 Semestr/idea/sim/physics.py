from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

from sim.bodies import BodiesConfig, step_bodies
from sim.dynamics import bh_pair_merge_weight, initialize_universe_positions, step_dynamics
from sim.layout import black_hole_layout_xy
from sim.life import LifeConfig, step_life
from sim.merge import merge_bhs
from sim.model import (
    BlackHole,
    BodyKind,
    CelestialBody,
    LifeStage,
    Multiverse,
    Universe,
    child_inner_information_caps_sum,
    universe_body_information_used,
)


@dataclass
class SimulationConfig:
    p_spawn_bh: float = 0.14
    p_spawn_bh_inner: float = 0.07
    bh_mass_mu: float = 0.5
    bh_mass_sigma: float = 0.35
    merge_pair_base_p: float = 0.065
    merge_mass_scale: float = 0.022
    merge_age_ramp: float = 0.0025
    p_nest: float = 0.075
    nest_mass_threshold: float = 1.15
    inner_information_per_bh_mass: float = 14.0
    scale_k: float = 0.06
    scale_noise: float = 0.008
    bodies: BodiesConfig = field(default_factory=BodiesConfig)
    life: LifeConfig = field(default_factory=LifeConfig)
    # N-body-lite + orbits (see sim.dynamics)
    dynamics_dt: float = 1.0
    gravity_softening: float = 95.0
    gravity_softening_bh_bh: float = 22.0
    grav_star_bh: float = 0.38
    grav_bh_bh: float = 2.15
    bh_velocity_damping: float = 0.9972
    bh_wander_accel: float = 0.11
    star_velocity_damping: float = 0.99955
    orbit_omega_scale: float = 0.026
    moon_orbit_omega_scale: float = 0.09
    absorb_radius_factor: float = 32.0
    absorb_spare_last_star_p: float = 0.9
    merge_contact_distance: float = 38.0
    merge_max_separation_mult: float = 1.55
    min_information_to_nest: float = 1.1
    universe_radius_scale: float = 2.05
    boundary_bounce_strength: float = 0.4
    max_bh_speed: float = 24.0
    max_free_body_speed: float = 18.0
    nebula_accretion_radius_factor: float = 64.0
    nebula_mass_loss_per_tick: float = 0.048
    nebula_min_mass: float = 0.034
    nebula_swallow_radius_mult: float = 1.24
    max_scale_root: float = 6.5
    max_scale_nested: float = 5.2
    # Root universe (level 0) does not grow in scale; nested universes still evolve.
    root_universe_scale_fixed: bool = True
    # Prefill body count cap (information target unchanged; prefer fewer, denser objects).
    prefill_max_bodies: int = 300


def _spawn_black_hole(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    p_bh = cfg.p_spawn_bh if u.id == 0 else cfg.p_spawn_bh_inner
    if m.rng.random() >= p_bh:
        return
    bid = m.alloc_bh_id()
    mass = max(0.15, m.rng.lognormvariate(cfg.bh_mass_mu, cfg.bh_mass_sigma))
    bh = BlackHole(id=bid, host=u, mass=mass)
    bh.pos_x, bh.pos_y = black_hole_layout_xy(bh, u)
    bh.render_prev_x, bh.render_prev_y = bh.pos_x, bh.pos_y
    bh.spatial_ready = True
    u.black_holes.append(bh)
    m.register_bh(bh)


def _try_merge_pairs(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    holes = list(u.black_holes)
    merges: List[Tuple[BlackHole, BlackHole]] = []
    for i, a in enumerate(holes):
        for b in holes[i + 1 :]:
            d = math.hypot(a.pos_x - b.pos_x, a.pos_y - b.pos_y)
            d_contact = cfg.merge_contact_distance * ((a.mass * b.mass) ** 0.35 + 0.12)
            if d > d_contact * cfg.merge_max_separation_mult:
                continue
            prod = (a.mass * b.mass) ** 0.5 * cfg.merge_mass_scale
            age_boost = 1.0 + min(2.2, cfg.merge_age_ramp * u.age)
            prox = bh_pair_merge_weight(a, b, cfg, u)
            p = (cfg.merge_pair_base_p + min(0.5, prod)) * age_boost * prox
            if m.rng.random() < p:
                merges.append((a, b))

    for a, b in merges:
        if a not in u.black_holes or b not in u.black_holes:
            continue
        s = a.mass + b.mass + 1e-9
        winner, loser = (a, b) if m.rng.random() < a.mass / s else (b, a)
        merge_bhs(m, winner, loser)


def _try_nest(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    for bh in list(u.black_holes):
        if bh.inner_universe is not None:
            continue
        if bh.mass < cfg.nest_mass_threshold:
            continue
        if bh.information_swallowed < cfg.min_information_to_nest:
            continue
        if m.rng.random() >= cfg.p_nest * min(1.5, bh.mass / cfg.nest_mass_threshold):
            continue
        uid = m.alloc_universe_id()
        others = child_inner_information_caps_sum(u)
        cap_desired = max(2.5, bh.mass * cfg.inner_information_per_bh_mass)
        cap = min(
            cap_desired,
            max(0.0, u.information_budget - others),
            bh.information_swallowed,
        )
        if cap < 2.0:
            continue
        bh.information_swallowed = max(0.0, bh.information_swallowed - cap)
        child = Universe(
            id=uid,
            parent_bh=bh,
            physics=u.physics.mutate_from(m.rng),
            scale=u.scale * (0.85 + 0.15 * m.rng.random()),
            age=0,
            information_budget=cap,
            latent_information=cap,
        )
        bh.inner_universe = child
        child.parent_bh = bh
        m.register_universe(child)


def _update_scale(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    if cfg.root_universe_scale_fixed and u.parent_bh is None:
        return
    total_m = sum(bh.mass for bh in u.black_holes) + 1e-6
    star_heat = sum(b.heat_index for b in u.bodies if b.kind == BodyKind.STAR)
    eps = cfg.scale_noise * (2 * m.rng.random() - 1)
    # Sublinear growth per tick to avoid blow-up over long runs.
    delta = cfg.scale_k * 0.02 * math.log1p(total_m) + 0.001 * star_heat + eps
    delta = max(-0.05, min(0.12, delta))
    # Inner universes also expand; weak coupling to parent layer's scale (not identical to L0 max).
    parent_boost = 1.0
    if u.parent_bh is not None:
        host = u.parent_bh.host
        parent_boost = 1.0 + 0.035 * math.log1p(host.scale)
    delta *= parent_boost
    u.scale = max(0.2, u.scale * (1.0 + delta))
    depth = 0
    cur: Universe = u
    while cur.parent_bh is not None:
        depth += 1
        cur = cur.parent_bh.host
    cap = cfg.max_scale_nested
    u.scale = min(u.scale, cap)


def universe_world_radius(u: Universe, cfg: SimulationConfig) -> float:
    from sim.layout import sector_scale

    return sector_scale(u) * cfg.universe_radius_scale


def _info_cost_spawn(kind: BodyKind, mass_index: float) -> float:
    if kind == BodyKind.STAR:
        return mass_index
    if kind == BodyKind.PLANET:
        return mass_index
    if kind == BodyKind.MOON:
        return mass_index * 0.35
    if kind == BodyKind.NEBULA:
        return mass_index * 0.45
    return mass_index * 0.55


def prefill_root_universe(m: Multiverse, cfg: SimulationConfig) -> None:
    """Dense matter in universe 0 up to most of the information budget."""
    u = m.root
    rng = m.rng
    target = u.information_budget * 0.998
    bc = cfg.bodies
    prefill_cap = cfg.prefill_max_bodies
    tries = 0
    while universe_body_information_used(u) < target and tries < 900 and len(u.bodies) < prefill_cap:
        tries += 1
        used = universe_body_information_used(u)
        stars = [b for b in u.bodies if b.kind == BodyKind.STAR]
        if not stars or (used < target * 0.3 and rng.random() < 0.5):
            mi = 0.5 + 1.35 * rng.random() if used < target * 0.85 else 0.35 + 0.95 * rng.random()
            if used + _info_cost_spawn(BodyKind.STAR, mi) > u.information_budget:
                break
            bid = m.alloc_body_id()
            st = CelestialBody(
                id=bid,
                universe=u,
                kind=BodyKind.STAR,
                mass_index=mi,
                heat_index=0.45 + u.physics.radiation_efficiency * 0.75 * rng.random(),
                stability=0.5 + 0.45 * rng.random(),
                distance_band=0.0,
                host_star_id=None,
                life_stage=LifeStage.NONE,
                habitability=0.0,
                life_complexity=0.0,
                exotic_tags=[],
            )
            u.bodies.append(st)
            m.register_body(st)
            continue
        star = rng.choice(stars)
        mi = 0.06 + 0.22 * rng.random()
        if used + _info_cost_spawn(BodyKind.PLANET, mi) > u.information_budget:
            break
        bid = m.alloc_body_id()
        pl = CelestialBody(
            id=bid,
            universe=u,
            kind=BodyKind.PLANET,
            mass_index=mi,
            heat_index=0.12 * star.heat_index,
            stability=0.42 + 0.48 * rng.random(),
            distance_band=rng.random(),
            host_star_id=star.id,
            life_stage=LifeStage.NONE,
            habitability=0.0,
            life_complexity=0.0,
            exotic_tags=[],
        )
        u.bodies.append(pl)
        m.register_body(pl)

    fills = 0
    while (
        universe_body_information_used(u) < target
        and fills < 600
        and len(u.bodies) < prefill_cap
    ):
        fills += 1
        used = universe_body_information_used(u)
        mi = 0.42 + 0.95 * rng.random()
        if used + _info_cost_spawn(BodyKind.NEBULA, mi) > u.information_budget:
            break
        bid = m.alloc_body_id()
        nb = CelestialBody(
            id=bid,
            universe=u,
            kind=BodyKind.NEBULA,
            mass_index=mi,
            heat_index=0.12,
            stability=0.35,
            distance_band=0.0,
            host_star_id=None,
            life_stage=LifeStage.NONE,
            habitability=0.0,
            life_complexity=0.0,
            exotic_tags=["nebula"],
        )
        u.bodies.append(nb)
        m.register_body(nb)

    initialize_universe_positions(m, m.root)


def step_multiverse(m: Multiverse, cfg: SimulationConfig | None = None) -> None:
    if cfg is None:
        cfg = SimulationConfig()

    for u in m.all_universes_bfs():
        step_dynamics(m, u, cfg)
        _spawn_black_hole(m, u, cfg)
        _try_merge_pairs(m, u, cfg)
        _try_nest(m, u, cfg)
        step_bodies(m, u, cfg)
        _update_scale(m, u, cfg)
        step_life(m, u, cfg)
        u.age += 1

    m.global_tick += 1
