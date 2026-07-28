from __future__ import annotations

from typing import List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.widgets import Slider

from sim.history import History
from sim.model import BodyKind, LifeStage, Multiverse, Universe


def _universe_label(u: Universe) -> str:
    life = " *" if u.has_life else ""
    n_plan = sum(1 for b in u.bodies if b.kind == BodyKind.PLANET)
    n_stars = sum(1 for b in u.bodies if b.kind == BodyKind.STAR)
    return f"U{u.id}\n★{n_stars}○{n_plan}{life}"


def _physics_short(u: Universe) -> str:
    p = u.physics
    return f"g={p.gravity_coupling:.2f} ex={p.exotic_permit:.2f}"


def build_nx_graph(m: Multiverse) -> Tuple[nx.DiGraph, dict, dict]:
    """Return graph, node colors, node labels."""
    G = nx.DiGraph()
    colors: dict = {}
    labels: dict = {}

    for u in m.all_universes_bfs():
        nid = f"U{u.id}"
        G.add_node(nid)
        labels[nid] = _universe_label(u)
        if u.has_life:
            colors[nid] = "#6ecf68"
        elif any(b.kind == BodyKind.PLANET and b.life_stage == LifeStage.PREBIOTIC for b in u.bodies):
            colors[nid] = "#e6d84a"
        else:
            colors[nid] = "#7eb8da"

        for bh in u.black_holes:
            bid = f"BH{bh.id}"
            G.add_node(bid)
            labels[bid] = f"BH{bh.id}\nm={bh.mass:.2f}"
            colors[bid] = "#1a1a1a"
            G.add_edge(nid, bid, kind="hosts")
            if bh.inner_universe is not None:
                iu = bh.inner_universe
                iid = f"U{iu.id}"
                G.add_edge(bid, iid, kind="inner")

    return G, colors, labels


def _layout(G: nx.DiGraph) -> dict:
    return nx.spring_layout(G, seed=42, k=0.35, iterations=50)


def run_interactive_view(m: Multiverse, history: History) -> None:
    """Matplotlib window: multiverse graph + scale(t) + time slider and arrow keys."""
    if not history.snapshots:
        history.record_initial(m)

    scales: List[float] = [s.root.scale for s in history.snapshots]
    nbh: List[int] = [len(s.root.black_holes) for s in history.snapshots]

    fig, (ax_graph, ax_plot) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[2.2, 1])
    plt.subplots_adjust(bottom=0.18, hspace=0.35)

    ax_slider = fig.add_axes((0.12, 0.06, 0.76, 0.03))
    snap_count = len(history.snapshots)
    slider = Slider(ax_slider, "step", 0, max(0, snap_count - 1), valinit=snap_count - 1, valstep=1)

    pos_cache: dict = {}

    def draw_state(state: Multiverse, idx: int) -> None:
        nonlocal pos_cache
        ax_graph.clear()
        ax_plot.clear()
        G, colors, labels = build_nx_graph(state)
        if not G.nodes:
            ax_graph.text(0.5, 0.5, "empty", ha="center")
        else:
            key = tuple(sorted(G.nodes()))
            if key not in pos_cache or set(pos_cache[key].keys()) != set(G.nodes()):
                pos_cache[key] = _layout(G)
            pos = {n: pos_cache[key][n] for n in G.nodes if n in pos_cache[key]}
            for n in G.nodes:
                if n not in pos:
                    pos[n] = (0.0, 0.0)
            node_color = [colors.get(n, "#cccccc") for n in G.nodes]
            nx.draw_networkx(
                G,
                pos,
                ax=ax_graph,
                labels=labels,
                node_color=node_color,
                font_size=7,
                node_size=900,
                font_color="black",
                edge_color="#555555",
                arrows=True,
                arrowsize=12,
            )
        ax_graph.set_title(f"Multiverse (step {idx})  {_physics_short(state.root)}")
        ax_graph.axis("off")

        xs = list(range(len(scales)))
        ax_plot.plot(xs, scales, "b-", label="root scale", alpha=0.8)
        ax_plot.plot(xs, nbh, "r--", label="N_BH @ L0", alpha=0.7)
        ax_plot.axvline(idx, color="green", alpha=0.6)
        ax_plot.set_xlabel("snapshot index")
        ax_plot.legend(loc="upper left", fontsize=8)
        ax_plot.grid(True, alpha=0.3)

        fig.canvas.draw_idle()

    current_idx = snap_count - 1

    def set_idx(i: int) -> None:
        nonlocal current_idx
        current_idx = int(max(0, min(snap_count - 1, i)))
        st = history.restore(current_idx)
        draw_state(st, current_idx)
        slider.set_val(current_idx)

    def on_slider_change(val: float) -> None:
        set_idx(int(val))

    slider.on_changed(on_slider_change)

    def on_key(event) -> None:
        if event.key in ("left", "a"):
            set_idx(current_idx - 1)
        elif event.key in ("right", "d"):
            set_idx(current_idx + 1)

    fig.canvas.mpl_connect("key_press_event", on_key)

    set_idx(current_idx)
    plt.show()
