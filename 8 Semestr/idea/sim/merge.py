from __future__ import annotations

from typing import TYPE_CHECKING

from sim.model import (
    BlackHole,
    BodyKind,
    LifeStage,
    Multiverse,
    Universe,
    child_inner_information_caps_sum,
    universe_body_information_used,
)

if TYPE_CHECKING:
    pass


def _downgrade_life(stage: LifeStage) -> LifeStage:
    order = [LifeStage.NONE, LifeStage.PREBIOTIC, LifeStage.LIFE, LifeStage.MULTICELLULAR]
    try:
        i = order.index(stage)
    except ValueError:
        return LifeStage.NONE
    return order[max(0, i - 1)]


def _merge_inner_universes(
    m: Multiverse,
    winner_bh: BlackHole,
    u1: Universe,
    u2: Universe,
    mass_w: float,
    mass_l: float,
) -> None:
    """Replace u1, u2 with a single merged universe attached to winner_bh."""
    new_id = m.alloc_universe_id()
    blended = u1.physics.blend(u2.physics, mass_w, mass_l, m.rng)
    host = winner_bh.host
    merged_raw = u1.information_budget + u2.information_budget
    s_all = child_inner_information_caps_sum(host)
    s_pair = u1.information_budget + u2.information_budget
    others = s_all - s_pair
    merged_budget = min(merged_raw, max(0.0, host.information_budget - others))
    merged_latent = u1.latent_information + u2.latent_information
    u_new = Universe(
        id=new_id,
        parent_bh=winner_bh,
        physics=blended,
        scale=(u1.scale + u2.scale) / 2,
        age=max(u1.age, u2.age),
        last_merger_tick=m.global_tick,
        information_budget=merged_budget,
        latent_information=merged_latent,
    )
    for bh in list(u1.black_holes) + list(u2.black_holes):
        bh.host = u_new
        u_new.black_holes.append(bh)
    u1.black_holes.clear()
    u2.black_holes.clear()

    cat = list(u1.bodies) + list(u2.bodies)
    u1.bodies.clear()
    u2.bodies.clear()
    p_cat = 0.12 * blended.merger_heating
    for b in cat:
        b.universe = u_new
        b.stability = max(0.05, b.stability * (0.82 + 0.1 * m.rng.random()))
        if b.kind == BodyKind.PLANET:
            if m.rng.random() < p_cat:
                b.life_stage = _downgrade_life(b.life_stage)
        u_new.bodies.append(b)

    used = universe_body_information_used(u_new)
    room = max(0.0, merged_budget - used)
    u_new.latent_information = min(u_new.latent_information, room)

    m.universes.pop(u1.id, None)
    m.universes.pop(u2.id, None)
    m.register_universe(u_new)
    winner_bh.inner_universe = u_new
    u_new.parent_bh = winner_bh


def merge_bhs(m: Multiverse, winner: BlackHole, loser: BlackHole) -> None:
    """Merge loser into winner; same host required."""
    if loser.host is not winner.host:
        raise ValueError("Black holes must share the same host universe")
    host = winner.host
    mass_w = winner.mass
    mass_l = loser.mass
    mt = mass_w + mass_l + 1e-9
    winner.pos_x = (winner.pos_x * mass_w + loser.pos_x * mass_l) / mt
    winner.pos_y = (winner.pos_y * mass_w + loser.pos_y * mass_l) / mt
    winner.vel_x = (winner.vel_x * mass_w + loser.vel_x * mass_l) / mt
    winner.vel_y = (winner.vel_y * mass_w + loser.vel_y * mass_l) / mt
    winner.render_prev_x, winner.render_prev_y = winner.pos_x, winner.pos_y
    winner.information_swallowed += loser.information_swallowed
    winner.mass = mass_w + mass_l + 0.01 * (2 * m.rng.random() - 1) * min(mass_w, mass_l)
    winner.mass = max(0.1, winner.mass)

    w_in = winner.inner_universe
    l_in = loser.inner_universe

    if w_in is None and l_in is None:
        pass
    elif w_in is not None and l_in is None:
        pass
    elif w_in is None and l_in is not None:
        winner.inner_universe = l_in
        l_in.parent_bh = winner
    else:
        assert w_in is not None and l_in is not None
        _merge_inner_universes(m, winner, w_in, l_in, mass_w, mass_l)

    host.last_merger_tick = m.global_tick
    host.black_holes.remove(loser)
    loser.inner_universe = None
    m.black_holes.pop(loser.id, None)
