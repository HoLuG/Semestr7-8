from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

import random


class BodyKind(Enum):
    STAR = auto()
    PLANET = auto()
    MOON = auto()
    NEBULA = auto()
    EXOTIC = auto()


class LifeStage(Enum):
    NONE = auto()
    PREBIOTIC = auto()
    LIFE = auto()
    MULTICELLULAR = auto()


@dataclass
class PhysicsProfile:
    """Dimensionless coefficients governing stochastic rules in a universe."""

    gravity_coupling: float
    radiation_efficiency: float
    structure_bias: float
    exotic_permit: float
    merger_heating: float
    chemistry_ease: float

    @staticmethod
    def random_profile(rng: random.Random) -> PhysicsProfile:
        def u(a: float = 0.25, b: float = 1.75) -> float:
            return a + (b - a) * rng.random()

        return PhysicsProfile(
            gravity_coupling=u(),
            radiation_efficiency=u(),
            structure_bias=u(),
            exotic_permit=u(0.1, 1.2),
            merger_heating=u(0.2, 1.5),
            chemistry_ease=u(0.3, 1.5),
        )

    def mutate_from(self, rng: random.Random, strength: float = 0.15) -> PhysicsProfile:
        def m(x: float) -> float:
            return max(0.05, min(2.5, x * (1.0 + strength * (2 * rng.random() - 1))))

        return PhysicsProfile(
            gravity_coupling=m(self.gravity_coupling),
            radiation_efficiency=m(self.radiation_efficiency),
            structure_bias=m(self.structure_bias),
            exotic_permit=m(self.exotic_permit),
            merger_heating=m(self.merger_heating),
            chemistry_ease=m(self.chemistry_ease),
        )

    def blend(self, other: PhysicsProfile, w_self: float, w_other: float, rng: random.Random) -> PhysicsProfile:
        t = w_self + w_other
        if t <= 0:
            t = 1.0
        noise = 0.02 * (2 * rng.random() - 1)

        def bl(a: float, b: float) -> float:
            v = (a * w_self + b * w_other) / t + noise
            return max(0.05, min(2.5, v))

        return PhysicsProfile(
            gravity_coupling=bl(self.gravity_coupling, other.gravity_coupling),
            radiation_efficiency=bl(self.radiation_efficiency, other.radiation_efficiency),
            structure_bias=bl(self.structure_bias, other.structure_bias),
            exotic_permit=bl(self.exotic_permit, other.exotic_permit),
            merger_heating=bl(self.merger_heating, other.merger_heating),
            chemistry_ease=bl(self.chemistry_ease, other.chemistry_ease),
        )


@dataclass
class CelestialBody:
    id: int
    universe: Universe
    kind: BodyKind
    mass_index: float
    heat_index: float
    stability: float
    distance_band: float
    host_star_id: Optional[int]
    life_stage: LifeStage
    habitability: float
    life_complexity: float
    host_planet_id: Optional[int] = None
    exotic_tags: List[str] = field(default_factory=list)
    # World-space kinematics + orbit phases (updated by sim.dynamics).
    pos_x: float = 0.0
    pos_y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    orbit_angle: float = 0.0
    moon_orbit_angle: float = 0.0
    spatial_ready: bool = False
    render_prev_x: float = 0.0
    render_prev_y: float = 0.0


@dataclass
class BlackHole:
    id: int
    host: Universe
    mass: float
    inner_universe: Optional[Universe] = None
    pos_x: float = 0.0
    pos_y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    # Information (matter budget units) swallowed from the host universe into this hole.
    information_swallowed: float = 0.0
    spatial_ready: bool = False
    render_prev_x: float = 0.0
    render_prev_y: float = 0.0


def body_information_value(b: CelestialBody) -> float:
    """One body's contribution to universe_body_information_used (same weights)."""
    if b.kind == BodyKind.STAR:
        return b.mass_index * 1.0
    if b.kind == BodyKind.PLANET:
        return b.mass_index * 1.0
    if b.kind == BodyKind.MOON:
        return b.mass_index * 0.35
    if b.kind == BodyKind.NEBULA:
        return b.mass_index * 0.45
    if b.kind == BodyKind.EXOTIC:
        return b.mass_index * 0.55
    return b.mass_index


def universe_body_information_used(u: Universe) -> float:
    """Dimensionless 'matter' in celestial bodies (sum of mass_index with kind weights)."""
    return sum(body_information_value(b) for b in u.bodies)


def child_inner_information_caps_sum(u: Universe) -> float:
    """Sum of information_budget over direct child universes (one inner per black hole)."""
    return sum(
        bh.inner_universe.information_budget
        for bh in u.black_holes
        if bh.inner_universe is not None
    )


@dataclass
class Universe:
    id: int
    parent_bh: Optional[BlackHole]
    black_holes: List[BlackHole] = field(default_factory=list)
    bodies: List[CelestialBody] = field(default_factory=list)
    physics: PhysicsProfile = field(default_factory=lambda: PhysicsProfile(1, 1, 1, 0.5, 1, 1))
    scale: float = 1.0
    age: int = 0
    last_merger_tick: int = -10**9
    # Max total body-information in this layer; inner universes get cap from parent BH mass.
    information_budget: float = 1e9
    # Information transferred from parent black hole into this layer but not yet in bodies (conservation).
    latent_information: float = 0.0

    @property
    def has_life(self) -> bool:
        return any(
            b.kind == BodyKind.PLANET and b.life_stage in (LifeStage.LIFE, LifeStage.MULTICELLULAR)
            for b in self.bodies
        )


@dataclass
class Multiverse:
    """Root simulation state: registry, RNG, global tick."""

    root: Universe
    universes: Dict[int, Universe] = field(default_factory=dict)
    black_holes: Dict[int, BlackHole] = field(default_factory=dict)
    bodies: Dict[int, CelestialBody] = field(default_factory=dict)
    next_universe_id: int = 1
    next_bh_id: int = 1
    next_body_id: int = 1
    rng: random.Random = field(default_factory=random.Random)
    global_tick: int = 0

    def register_universe(self, u: Universe) -> None:
        self.universes[u.id] = u

    def register_bh(self, bh: BlackHole) -> None:
        self.black_holes[bh.id] = bh

    def register_body(self, b: CelestialBody) -> None:
        self.bodies[b.id] = b

    def alloc_universe_id(self) -> int:
        i = self.next_universe_id
        self.next_universe_id += 1
        return i

    def alloc_bh_id(self) -> int:
        i = self.next_bh_id
        self.next_bh_id += 1
        return i

    def alloc_body_id(self) -> int:
        i = self.next_body_id
        self.next_body_id += 1
        return i

    def all_universes_bfs(self) -> List[Universe]:
        out: List[Universe] = []
        stack = [self.root]
        seen = set()
        while stack:
            u = stack.pop()
            if u.id in seen:
                continue
            seen.add(u.id)
            out.append(u)
            for bh in u.black_holes:
                if bh.inner_universe is not None:
                    stack.append(bh.inner_universe)
        return out


def total_information_in_multiverse(m: Multiverse) -> float:
    """Bodies + latent pools in every universe + information_swallowed on every black hole (conserved total)."""
    t = 0.0
    for u in m.all_universes_bfs():
        t += universe_body_information_used(u)
        t += u.latent_information
        for bh in u.black_holes:
            t += bh.information_swallowed
    return t


def create_root_multiverse(
    seed: Optional[int] = None,
    *,
    root_information_budget: float = 92.0,
) -> Multiverse:
    rng = random.Random(seed)
    root = Universe(
        id=0,
        parent_bh=None,
        physics=PhysicsProfile.random_profile(rng),
        information_budget=root_information_budget,
    )
    m = Multiverse(root=root, rng=rng, next_universe_id=1)
    m.register_universe(root)
    return m
