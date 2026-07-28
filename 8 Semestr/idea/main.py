from __future__ import annotations

import argparse
import sys

from sim.history import History
from sim.model import create_root_multiverse
from sim.physics import SimulationConfig, prefill_root_universe, step_multiverse


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Nested universe simulation (multiverse + black holes + life).")
    p.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Optional: pre-run this many steps before opening the viewer (default 0 = start from t=0 in the game).",
    )
    p.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible).")
    p.add_argument("--snapshot-every", type=int, default=1, help="Record history every N ticks (memory vs resolution).")
    p.add_argument("--max-history", type=int, default=None, help="Keep only last M snapshots (sliding window).")
    p.add_argument("--no-show", action="store_true", help="Do not open any viewer (batch only).")
    p.add_argument(
        "--view",
        choices=("pygame", "matplotlib"),
        default="pygame",
        help="Interactive UI: pygame game (default) or matplotlib graph.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    m = create_root_multiverse(args.seed)
    cfg = SimulationConfig()
    prefill_root_universe(m, cfg)
    hist = History(snapshot_every=args.snapshot_every, max_history=args.max_history)
    hist.record_initial(m)

    for _ in range(args.steps):
        step_multiverse(m, cfg)
        hist.record(m)

    if args.no_show:
        print(
            f"tick={m.global_tick} root_BH={len(m.root.black_holes)} "
            f"scale={m.root.scale:.3f} has_life={m.root.has_life} universes={len(m.universes)}"
        )
        return

    if args.view == "pygame":
        try:
            from viz.pygame_game import run_pygame_game
        except ImportError as e:
            print("pygame required: pip install pygame", e, file=sys.stderr)
            sys.exit(1)
        run_pygame_game(m, hist, cfg, start_auto_play=args.steps == 0)
        return

    try:
        from viz.graph_view import run_interactive_view
    except ImportError as e:
        print("matplotlib/networkx required for matplotlib view:", e, file=sys.stderr)
        sys.exit(1)
    run_interactive_view(m, hist)


if __name__ == "__main__":
    main()
