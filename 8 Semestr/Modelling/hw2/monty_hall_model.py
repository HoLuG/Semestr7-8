"""
Generalized Monty Hall: N doors, host opens K empty doors,
final stage: probability s to stay, (1-s) to switch.
Theoretical probabilities follow from Bayes' formula for events A (prize behind
initial choice) and B (host opens K empty doors).
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass

import numpy as np


def theoretical_win_prob(N: int, K: int, prob_stay: float) -> float:
    """Theoretical win probability (uniform choice among closed doors when switching)."""
    if N < 3 or K < 1 or K > N - 2:
        raise ValueError("require N>=3 and 1<=K<=N-2")
    if not 0.0 <= prob_stay <= 1.0:
        raise ValueError("prob_stay must be in [0,1]")
    p_stay = 1.0 / N
    p_switch = (N - 1) / (N * (N - 1 - K))
    return prob_stay * p_stay + (1.0 - prob_stay) * p_switch


def posterior_choice_has_prize(N: int, K: int) -> float:
    """
    Posterior P(A|B) for generalized Monty Hall under symmetry assumptions.

    A: prize is behind player's initial choice.
    B: host opens exactly K empty doors, not opening the prize door nor the chosen door,
       choosing uniformly among all valid sets.
    """
    if N < 3 or K < 1 or K > N - 2:
        raise ValueError("require N>=3 and 1<=K<=N-2")

    c1 = math.comb(N - 1, K)
    c2 = math.comb(N - 2, K)
    num = (1.0 / N) * (1.0 / c1)
    den = num + ((N - 1) / N) * (1.0 / c2)
    return num / den


def theoretical_win_prob_bayes_opt(N: int, K: int) -> float:
    """
    Optimal (Bayesian) strategy after observing the host's action:
    compare posterior of staying vs any other closed door.
    """
    p_choice = posterior_choice_has_prize(N, K)
    p_alt = (1.0 - p_choice) / (N - 1 - K)
    return (1.0 - p_choice) if (p_alt > p_choice) else p_choice


def run_monte_carlo(
    N: int,
    K: int,
    prob_stay: float,
    n_trials: int,
    seed: int | None = 42,
) -> tuple[np.ndarray, float]:
    """Monte Carlo: array of 0/1 wins and sample mean."""
    rng = np.random.default_rng(seed)
    prize = rng.integers(0, N, size=n_trials)
    choice = rng.integers(0, N, size=n_trials)
    stay = rng.random(n_trials) < prob_stay
    wins = np.zeros(n_trials, dtype=np.int8)
    for i in range(n_trials):
        c_open = [d for d in range(N) if d != choice[i] and d != prize[i]]
        idx = rng.choice(len(c_open), size=K, replace=False)
        opened = {c_open[int(j)] for j in idx}
        closed = [d for d in range(N) if d not in opened]
        if stay[i]:
            final_door = int(choice[i])
        else:
            alt = [d for d in closed if d != choice[i]]
            final_door = int(choice[i]) if not alt else int(rng.choice(alt))
        wins[i] = 1 if final_door == prize[i] else 0
    return wins, float(wins.mean())


def run_monte_carlo_strategy(
    N: int,
    K: int,
    n_trials: int,
    strategy: str,
    prob_stay: float = 0.5,
    seed: int | None = 42,
) -> tuple[np.ndarray, float]:
    """
    strategy:
      - 'stay'   : always keep initial choice
      - 'switch' : always switch to a random other closed door
      - 'mixed'  : keep with probability prob_stay, switch otherwise
      - 'bayes'  : Bayes-optimal decision based on A,B posterior (depends only on N,K)
    """
    strategy = strategy.lower().strip()
    if strategy not in {"stay", "switch", "mixed", "bayes"}:
        raise ValueError("strategy must be one of: stay, switch, mixed, bayes")

    if strategy == "stay":
        return run_monte_carlo(N, K, prob_stay=1.0, n_trials=n_trials, seed=seed)
    if strategy == "switch":
        return run_monte_carlo(N, K, prob_stay=0.0, n_trials=n_trials, seed=seed)

    if strategy == "mixed":
        return run_monte_carlo(N, K, prob_stay=prob_stay, n_trials=n_trials, seed=seed)

    p_choice = posterior_choice_has_prize(N, K)
    p_alt = (1.0 - p_choice) / (N - 1 - K)
    do_switch = p_alt > p_choice
    return run_monte_carlo(N, K, prob_stay=0.0 if do_switch else 1.0, n_trials=n_trials, seed=seed)


def cdf_distance_bernoulli(p_hat: float, p0: float) -> float:
    """sup_x |F_n(x) - F(x)| for indicator outcome equals |p_hat - p0|."""
    return abs(p_hat - p0)


def ks_critical_approx(alpha: float, n: int) -> float:
    """Reference scale D_cr ~ k_alpha / sqrt(n) (continuous case; used as order-of-magnitude)."""
    k_table = {0.10: 1.23, 0.05: 1.36, 0.02: 1.52, 0.01: 1.63}
    if alpha not in k_table:
        raise ValueError(f"alpha must be one of {list(k_table)}")
    return k_table[alpha] / math.sqrt(n)


@dataclass
class AdequacyRow:
    strategy: str
    n: int
    wins: int
    p_hat: float
    p_theory_bayes: float
    abs_diff: float
    D_n: float
    D_crit_005: float


def adequacy_monty_hall_classic(
    n_trials: int = 200_000, seed: int = 42
) -> list[AdequacyRow]:
    """N=3, K=1: compare MC to theoretical P(W) from the same Bayes line (1/3 and 2/3)."""
    rows: list[AdequacyRow] = []
    for name, s, p0 in [
        ("stay (s=1)", 1.0, theoretical_win_prob(3, 1, 1.0)),
        ("switch (s=0)", 0.0, theoretical_win_prob(3, 1, 0.0)),
    ]:
        wins_arr, _ = run_monte_carlo(3, 1, s, n_trials, seed=seed + hash(name) % 10000)
        k = int(wins_arr.sum())
        p_hat = k / n_trials
        D_n = cdf_distance_bernoulli(p_hat, p0)
        D_cr = ks_critical_approx(0.05, n_trials)
        rows.append(
            AdequacyRow(
                strategy=name,
                n=n_trials,
                wins=k,
                p_hat=p_hat,
                p_theory_bayes=p0,
                abs_diff=abs(p_hat - p0),
                D_n=D_n,
                D_crit_005=D_cr,
            )
        )
    return rows


def grid_experiment(
    n_trials: int,
    prob_stay: float,
    seed: int,
) -> list[dict]:
    """Grid N=3..10, K=1..N-2."""
    out = []
    for N in range(3, 11):
        for K in range(1, N - 1):
            if K > N - 2:
                continue
            p_th = theoretical_win_prob(N, K, prob_stay)
            _, p_mc = run_monte_carlo(N, K, prob_stay, n_trials, seed=seed + N * 100 + K)
            out.append(
                {
                    "N": N,
                    "K": K,
                    "p_theory": p_th,
                    "p_mc": p_mc,
                    "abs_diff": abs(p_th - p_mc),
                }
            )
    return out


def sweep_n_trials(
    N: int,
    K: int,
    prob_stay: float,
    n_list: list[int],
    seed: int,
) -> list[dict]:
    """How |p_hat - p_theory| shrinks as n grows (mixed strategy)."""
    p_theory = theoretical_win_prob(N, K, prob_stay)
    out = []
    for n in n_list:
        _, p_mc = run_monte_carlo(N, K, prob_stay, n, seed=seed + n)
        out.append(
            {
                "N": N,
                "K": K,
                "prob_stay": prob_stay,
                "n_trials": n,
                "p_theory": p_theory,
                "p_mc": p_mc,
                "abs_diff": abs(p_theory - p_mc),
            }
        )
    return out


def sweep_prob_stay(
    N: int,
    K: int,
    s_list: list[float],
    n_trials: int,
    seed: int,
) -> list[dict]:
    """Different ratios stay vs switch for fixed N, K."""
    out = []
    for s in s_list:
        p_th = theoretical_win_prob(N, K, s)
        _, p_mc = run_monte_carlo(N, K, s, n_trials, seed=seed + int(s * 10000))
        out.append(
            {
                "N": N,
                "K": K,
                "prob_stay": s,
                "p_theory": p_th,
                "p_mc": p_mc,
                "abs_diff": abs(p_th - p_mc),
            }
        )
    return out


def plot_figures(out_dir: str, seed: int = 42) -> None:
    import matplotlib.pyplot as plt

    os.makedirs(out_dir, exist_ok=True)

    N = 7
    Kmax = N - 2
    s_vals = np.linspace(0, 1, 101)
    plt.figure(figsize=(7, 4.5))
    for K in range(1, Kmax + 1):
        ys = [theoretical_win_prob(N, K, float(s)) for s in s_vals]
        plt.plot(s_vals, ys, label=f"K={K}")
    plt.xlabel(r"stay probability $s$")
    plt.ylabel(r"$P(\mathrm{win})$")
    plt.title(rf"Theory: $N={N}$, mixed strategy")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "hw2_prob_vs_switch.png"), dpi=150)
    plt.close()

    n_mc = 80_000
    prob_stay = 0.5
    Ks = list(range(1, N - 1))
    p_th = [theoretical_win_prob(N, K, prob_stay) for K in Ks]
    p_mc = []
    for K in Ks:
        _, ph = run_monte_carlo(N, K, prob_stay, n_mc, seed=seed + K)
        p_mc.append(ph)
    plt.figure(figsize=(7, 4.5))
    plt.plot(Ks, p_th, "o-", label="analytic")
    plt.plot(Ks, p_mc, "s--", label=f"Monte Carlo ($n={n_mc}$)")
    plt.xlabel(r"$K$")
    plt.ylabel(r"$P(\mathrm{win})$")
    plt.title(rf"$N={N}$, $s={prob_stay}$")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "hw2_theory_vs_mc_N7.png"), dpi=150)
    plt.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n-trials", type=int, default=200_000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--json-out", type=str, default="hw2_results.json")
    p.add_argument("--plots", action="store_true")
    p.add_argument(
        "--strategy",
        type=str,
        default="mixed",
        help="stay|switch|mixed|bayes (default: mixed)",
    )
    p.add_argument(
        "--prob-stay",
        type=float,
        default=0.5,
        help="used only for strategy=mixed",
    )
    args = p.parse_args()

    rows = adequacy_monty_hall_classic(n_trials=args.n_trials, seed=args.seed)
    grid_n = min(args.n_trials, 50_000)
    grid = grid_experiment(
        n_trials=grid_n,
        prob_stay=args.prob_stay,
        seed=args.seed,
    )

    n_sweep_list = [10, 100, 1000, 10000, 50000, 100000]
    sweep_n = sweep_n_trials(
        N=7, K=3, prob_stay=0.5, n_list=n_sweep_list, seed=args.seed
    )
    s_sweep_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    sweep_s = sweep_prob_stay(
        N=7, K=3, s_list=s_sweep_list, n_trials=50_000, seed=args.seed
    )

    payload = {
        "adequacy_classic": [r.__dict__ for r in rows],
        "grid_mixed_s0.5": grid,
        "sweep_n_trials_N7_K3_s0.5": sweep_n,
        "sweep_prob_stay_N7_K3_n50000": sweep_s,
        "posterior_P_A_given_B_N3_K1": posterior_choice_has_prize(3, 1),
        "n_trials_adequacy": args.n_trials,
        "n_trials_grid": grid_n,
        "strategy": args.strategy,
        "prob_stay": args.prob_stay,
    }
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("=== Adequacy (N=3, K=1), Bayes-theory vs MC ===")
    for r in rows:
        print(
            f"{r.strategy}: wins={r.wins}/{r.n}, p_hat={r.p_hat:.6f}, "
            f"p_theory={r.p_theory_bayes:.6f}, |diff|={r.abs_diff:.6f}, "
            f"D_n={r.D_n:.6f}, D_cr(0.05)~{r.D_crit_005:.6f}"
        )

    if args.plots:
        plot_figures("images", seed=args.seed)
        print("Plots saved to images/")

    print(f"\nJSON: {args.json_out}")


if __name__ == "__main__":
    main()
