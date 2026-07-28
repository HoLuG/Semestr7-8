from viz.graph_view import run_interactive_view


def run_pygame_game(m, hist, cfg=None, **kwargs):
    from viz.pygame_game import run_pygame_game as _run

    return _run(m, hist, cfg, **kwargs)


__all__ = ["run_interactive_view", "run_pygame_game"]
