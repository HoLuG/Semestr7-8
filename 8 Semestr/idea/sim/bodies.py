from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from sim.model import BodyKind, CelestialBody, LifeStage, Universe, universe_body_information_used

if TYPE_CHECKING:
    from sim.model import Multiverse
    from sim.physics import SimulationConfig


@dataclass
class BodiesConfig:
    p_spawn_star: float = 0.08
    p_spawn_planet_per_star: float = 0.12
    max_planets_per_star: int = 6
    p_spawn_moon: float = 0.03
    p_spawn_nebula: float = 0.04
    p_spawn_exotic: float = 0.02
    max_bodies_per_universe: int = 120
    max_nebulae_per_universe: int = 10


EXOTIC_PRESETS = [
    ("crystal_sun", ["boost_radiation", "stabilize_orbits"]),
    ("stable_strand", ["reduce_chaos"]),
    ("entropy_sink", ["damp_life", "cool_stars"]),
    ("mirror_core", ["reflect_merger", "boost_chemistry"]),
]


def _stars_in_universe(u: Universe) -> List[CelestialBody]:
    return [b for b in u.bodies if b.kind == BodyKind.STAR]


def _information_cost(kind: BodyKind, mass_index: float) -> float:
    if kind == BodyKind.STAR:
        return mass_index
    if kind == BodyKind.PLANET:
        return mass_index
    if kind == BodyKind.MOON:
        return mass_index * 0.35
    if kind == BodyKind.NEBULA:
        return mass_index * 0.45
    return mass_index * 0.55


def _can_spawn(u: Universe, cost: float) -> bool:
    if universe_body_information_used(u) + cost > u.information_budget + 1e-6:
        return False
    # Nested worlds: new matter may only crystallize from latent pool transferred from the parent BH.
    if u.parent_bh is not None:
        return cost <= u.latent_information + 1e-6
    return True


def _consume_latent_on_spawn(u: Universe, kind: BodyKind, mass_index: float) -> None:
    """Move spawn cost from latent pool (transferred from parent BH) into bodies."""
    c = _information_cost(kind, mass_index)
    if u.latent_information > 0:
        u.latent_information = max(0.0, u.latent_information - min(u.latent_information, c))


def step_bodies(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    rng = m.rng
    p = u.physics
    bc = cfg.bodies

    if len(u.bodies) >= bc.max_bodies_per_universe:
        return

    struct = p.structure_bias
    chaos = max(0.1, struct)
    p_star = bc.p_spawn_star * (0.4 + 0.6 / chaos) * (0.5 + 0.5 * min(u.scale, 3.0) / 3.0)

    if rng.random() < p_star:
        mi = 0.3 + 1.2 * rng.random()
        if _can_spawn(u, _information_cost(BodyKind.STAR, mi)):
            bid = m.alloc_body_id()
            body = CelestialBody(
                id=bid,
                universe=u,
                kind=BodyKind.STAR,
                mass_index=mi,
                heat_index=0.4 + p.radiation_efficiency * 0.8 * rng.random(),
                stability=0.5 + 0.5 * rng.random(),
                distance_band=0.0,
                host_star_id=None,
                life_stage=LifeStage.NONE,
                habitability=0.0,
                life_complexity=0.0,
                exotic_tags=[],
            )
            u.bodies.append(body)
            m.register_body(body)
            _consume_latent_on_spawn(u, BodyKind.STAR, mi)
            if len(u.bodies) >= bc.max_bodies_per_universe:
                return

    stars = _stars_in_universe(u)
    for star in stars:
        n_planets = sum(1 for b in u.bodies if b.kind == BodyKind.PLANET and b.host_star_id == star.id)
        if n_planets >= bc.max_planets_per_star:
            continue
        p_planet = (
            bc.p_spawn_planet_per_star
            * (0.3 + 0.7 * p.gravity_coupling / 1.5)
            * (1.0 - 0.15 * n_planets)
        )
        if rng.random() < p_planet:
            mi = 0.05 + 0.25 * rng.random()
            if not _can_spawn(u, _information_cost(BodyKind.PLANET, mi)):
                continue
            bid = m.alloc_body_id()
            dist = rng.random()
            body = CelestialBody(
                id=bid,
                universe=u,
                kind=BodyKind.PLANET,
                mass_index=mi,
                heat_index=0.1 * star.heat_index,
                stability=0.4 + 0.5 * rng.random(),
                distance_band=dist,
                host_star_id=star.id,
                life_stage=LifeStage.NONE,
                habitability=0.0,
                life_complexity=0.0,
                exotic_tags=[],
            )
            u.bodies.append(body)
            m.register_body(body)
            _consume_latent_on_spawn(u, BodyKind.PLANET, mi)
            if len(u.bodies) >= bc.max_bodies_per_universe:
                return

    if stars and rng.random() < bc.p_spawn_moon:
        star = rng.choice(stars)
        planet_hosts = [
            p for p in u.bodies if p.kind == BodyKind.PLANET and p.host_star_id == star.id
        ]
        if planet_hosts:
            pl = rng.choice(planet_hosts)
            mi = 0.02 + 0.05 * rng.random()
            if _can_spawn(u, _information_cost(BodyKind.MOON, mi)):
                bid = m.alloc_body_id()
                body = CelestialBody(
                    id=bid,
                    universe=u,
                    kind=BodyKind.MOON,
                    mass_index=mi,
                    heat_index=0.05,
                    stability=0.5 + 0.4 * rng.random(),
                    distance_band=rng.random(),
                    host_star_id=star.id,
                    host_planet_id=pl.id,
                    life_stage=LifeStage.NONE,
                    habitability=0.0,
                    life_complexity=0.0,
                    exotic_tags=[],
                )
                u.bodies.append(body)
                m.register_body(body)
                _consume_latent_on_spawn(u, BodyKind.MOON, mi)

    n_neb = sum(1 for b in u.bodies if b.kind == BodyKind.NEBULA)
    p_neb = (
        bc.p_spawn_nebula
        * (0.5 + 0.5 * p.structure_bias)
        * max(0.1, 1.0 - 0.09 * n_neb)
    )
    if n_neb < bc.max_nebulae_per_universe and rng.random() < p_neb:
        mi = 0.2 + 0.5 * rng.random()
        if _can_spawn(u, _information_cost(BodyKind.NEBULA, mi)):
            bid = m.alloc_body_id()
            body = CelestialBody(
                id=bid,
                universe=u,
                kind=BodyKind.NEBULA,
                mass_index=mi,
                heat_index=0.15,
                stability=0.3,
                distance_band=0.0,
                host_star_id=None,
                life_stage=LifeStage.NONE,
                habitability=0.0,
                life_complexity=0.0,
                exotic_tags=["nebula"],
            )
            u.bodies.append(body)
            m.register_body(body)
            _consume_latent_on_spawn(u, BodyKind.NEBULA, mi)

    p_ex = bc.p_spawn_exotic * p.exotic_permit
    if rng.random() < p_ex:
        name, tags = rng.choice(EXOTIC_PRESETS)
        mi = 0.1 + 0.3 * rng.random()
        if not _can_spawn(u, _information_cost(BodyKind.EXOTIC, mi)):
            return
        bid = m.alloc_body_id()
        body = CelestialBody(
            id=bid,
            universe=u,
            kind=BodyKind.EXOTIC,
            mass_index=mi,
            heat_index=0.2 + 0.3 * rng.random(),
            stability=0.2 + 0.5 * rng.random(),
            distance_band=rng.random(),
            host_star_id=(rng.choice(stars).id if stars else None),
            life_stage=LifeStage.NONE,
            habitability=0.0,
            life_complexity=0.0,
            exotic_tags=[name, *tags],
        )
        u.bodies.append(body)
        m.register_body(body)
        _consume_latent_on_spawn(u, BodyKind.EXOTIC, mi)
