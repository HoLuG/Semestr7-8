from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

from sim.model import BodyKind, CelestialBody, LifeStage, Universe

if TYPE_CHECKING:
    from sim.model import Multiverse
    from sim.physics import SimulationConfig


@dataclass
class LifeConfig:
    prebiotic_base_p: float = 0.04
    life_base_p: float = 0.03
    multicellular_p: float = 0.015
    merger_stability_penalty: float = 0.12


def _find_star(u: Universe, star_id: Optional[int]) -> Optional[CelestialBody]:
    if star_id is None:
        return None
    for b in u.bodies:
        if b.id == star_id and b.kind == BodyKind.STAR:
            return b
    return None


def _exotic_modifiers(u: Universe) -> Dict[str, float]:
    out: Dict[str, float] = {
        "life_boost": 1.0,
        "chem_boost": 1.0,
        "stab_boost": 1.0,
    }
    for b in u.bodies:
        if b.kind != BodyKind.EXOTIC:
            continue
        for t in b.exotic_tags:
            if t == "boost_radiation":
                out["chem_boost"] += 0.08
            elif t == "stabilize_orbits":
                out["stab_boost"] += 0.1
            elif t == "damp_life":
                out["life_boost"] -= 0.15
            elif t == "cool_stars":
                out["chem_boost"] -= 0.05
            elif t == "reflect_merger":
                out["stab_boost"] += 0.12
            elif t == "boost_chemistry":
                out["chem_boost"] += 0.15
    for k in out:
        out[k] = max(0.05, min(2.5, out[k]))
    return out


def _habitable_zone_center(physics) -> float:
    return 0.42 + 0.08 * (physics.chemistry_ease - 1.0)


def _habitable_zone_width(physics) -> float:
    return max(0.08, 0.28 / max(0.2, physics.structure_bias))


def compute_planet_habitability(m: Multiverse, u: Universe, planet: CelestialBody) -> float:
    if planet.kind != BodyKind.PLANET:
        return 0.0
    phys = u.physics
    star = _find_star(u, planet.host_star_id)
    ex = _exotic_modifiers(u)

    if star is None:
        base = 0.15 * phys.chemistry_ease * ex["chem_boost"]
    else:
        hz_c = _habitable_zone_center(phys)
        hz_w = _habitable_zone_width(phys)
        dist_term = 1.0 - min(1.0, abs(planet.distance_band - hz_c) / hz_w)
        heat_ok = min(1.0, star.heat_index * phys.radiation_efficiency)
        base = max(0.0, dist_term) * (0.3 + 0.7 * heat_ok) * phys.chemistry_ease * ex["chem_boost"]

    merger_age = m.global_tick - u.last_merger_tick
    calm = min(1.0, merger_age / 25.0)
    base *= (0.4 + 0.6 * calm) * (0.5 + 0.5 * planet.stability) * ex["stab_boost"]
    base *= ex["life_boost"]
    return max(0.0, min(1.0, base))


def step_life(m: Multiverse, u: Universe, cfg: SimulationConfig) -> None:
    rng = m.rng
    lc = cfg.life
    for planet in u.bodies:
        if planet.kind != BodyKind.PLANET:
            continue
        planet.habitability = compute_planet_habitability(m, u, planet)
        h = planet.habitability

        if planet.life_stage == LifeStage.NONE and h > 0.08:
            p = lc.prebiotic_base_p * h * u.physics.chemistry_ease
            if rng.random() < p:
                planet.life_stage = LifeStage.PREBIOTIC

        elif planet.life_stage == LifeStage.PREBIOTIC:
            p = lc.life_base_p * h
            if rng.random() < p:
                planet.life_stage = LifeStage.LIFE
                planet.life_complexity = 0.1 + 0.3 * rng.random()

        elif planet.life_stage == LifeStage.LIFE:
            p = lc.multicellular_p * h * planet.life_complexity
            if rng.random() < p:
                planet.life_stage = LifeStage.MULTICELLULAR
                planet.life_complexity = min(1.0, planet.life_complexity + 0.2 * rng.random())
