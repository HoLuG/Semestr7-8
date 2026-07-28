import argparse
import csv
import os
import sys

def parse_args():
    p = argparse.ArgumentParser(description="Plot Loop/Select benchmark results")
    p.add_argument("--csv", default=None, help="Path to CSV file (auto-detected if omitted)")
    p.add_argument("--out", default=None, help="Output file (.png/.pdf/.svg). Shows window if omitted.")
    p.add_argument("--dpi", type=int, default=150, help="DPI for raster output (default: 150)")
    p.add_argument("--lang", choices=["ru", "en"], default="ru", help="Language for labels")
    return p.parse_args()


def find_csv():
    candidates = [
        "bench/loop-select-results.csv",
        "loop-select-results.csv",
        os.path.join(os.path.dirname(__file__), "loop-select-results.csv"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            def parse(v):
                if v in ("", None, '""', "—"):
                    return None
                try:
                    return float(v.replace(",", "."))
                except ValueError:
                    return None
            rows.append({
                "N":       int(row["N"]),
                "ours":    parse(row.get("ours_ms")),
                "pz":      parse(row.get("pz_ms")),
                "r5j":     parse(row.get("r5j_ms")),
            })
    return rows


def fit_quadratic(xs, ys):
    import numpy as np
    valid = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if len(valid) < 3:
        return None
    xv = [v[0] for v in valid]
    yv = [v[1] for v in valid]
    return np.polyfit(xv, yv, 2)


def fit_linear(xs, ys):
    import numpy as np
    valid = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if len(valid) < 2:
        return None
    xv = [v[0] for v in valid]
    yv = [v[1] for v in valid]
    return np.polyfit(xv, yv, 1)


def main():
    args = parse_args()

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("ERROR: matplotlib and numpy are required.\n  pip install matplotlib numpy", file=sys.stderr)
        sys.exit(1)

    if args.out:
        matplotlib.use("Agg")

    csv_path = args.csv or find_csv()
    if csv_path is None:
        print("ERROR: CSV not found. Run loop-select-bench.ps1 first.", file=sys.stderr)
        sys.exit(1)

    rows = load_csv(csv_path)
    if not rows:
        print("ERROR: CSV is empty.", file=sys.stderr)
        sys.exit(1)

    Ns   = [r["N"]    for r in rows]
    ours = [r["ours"] for r in rows]
    pz   = [r["pz"]   for r in rows]
    r5j  = [r["r5j"]  for r in rows]

    has_pz  = any(v is not None for v in pz)
    has_r5j = any(v is not None for v in r5j)

    Nmax_data = max(Ns)
    Nfit = np.linspace(min(Ns), Nmax_data * 1.2, 300)

    fig, ax = plt.subplots(figsize=(9, 6))

    COLORS = {
        "ours": "#1f77b4",
        "pz":   "#d62728",
        "r5j":  "#ff7f0e",
    }

    if args.lang == "ru":
        labels = {
            "ours":       "refal5q-impl (ВКР, bootstrapped deque)",
            "pz":         "Refal-5 PZ (C, связный список)",
            "r5j":        "Refal-5J (Java, массивный список)",
            "ours_fit":   "O(N) — аппроксимация",
            "pz_fit":     "O(N²) — аппроксимация",
            "r5j_fit":    "O(N²) — аппроксимация",
            "title":      "Бенчмарк Loop/Select: сравнение асимптотики",
            "xlabel":     "Размер входа N",
            "ylabel":     "Время выполнения (мс)",
            "complexity": "Асимптотика: наша реализация O(N), связные списки O(N²)",
        }
    else:
        labels = {
            "ours":       "refal5q-impl (thesis, bootstrapped deque)",
            "pz":         "Refal-5 PZ (C, linked list)",
            "r5j":        "Refal-5J (Java, array list)",
            "ours_fit":   "O(N) fit",
            "pz_fit":     "O(N²) fit",
            "r5j_fit":    "O(N²) fit",
            "title":      "Loop/Select benchmark: asymptotic comparison",
            "xlabel":     "Input size N",
            "ylabel":     "Execution time (ms)",
            "complexity": "Our impl: O(N), linked-list impls: O(N²)",
        }

    def scatter_series(vals, key, label, marker="o"):
        valid_x = [x for x, y in zip(Ns, vals) if y is not None]
        valid_y = [y for y in vals if y is not None]
        if valid_y:
            ax.scatter(valid_x, valid_y, color=COLORS[key], marker=marker,
                       s=60, zorder=5, label=label)
        return valid_x, valid_y

    scatter_series(ours, "ours", labels["ours"])

    fit_our = fit_linear(Ns, ours)
    if fit_our is not None:
        y_fit = np.polyval(fit_our, Nfit)
        ax.plot(Nfit, y_fit, color=COLORS["ours"], linestyle="--",
                linewidth=1.5, alpha=0.7, label=labels["ours_fit"])

    if has_pz:
        scatter_series(pz, "pz", labels["pz"], marker="s")
        fit_pz = fit_quadratic(Ns, pz)
        if fit_pz is not None:
            y_fit = np.polyval(fit_pz, Nfit)
            ax.plot(Nfit, y_fit, color=COLORS["pz"], linestyle="--",
                    linewidth=1.5, alpha=0.7, label=labels["pz_fit"])

    if has_r5j:
        scatter_series(r5j, "r5j", labels["r5j"], marker="^")
        fit_r5j = fit_quadratic(Ns, r5j)
        if fit_r5j is not None:
            y_fit = np.polyval(fit_r5j, Nfit)
            ax.plot(Nfit, y_fit, color=COLORS["r5j"], linestyle=":",
                    linewidth=1.5, alpha=0.7, label=labels["r5j_fit"])

    ax.set_title(labels["title"], fontsize=14, pad=12)
    ax.set_xlabel(labels["xlabel"], fontsize=12)
    ax.set_ylabel(labels["ylabel"], fontsize=12)
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    fig.text(0.5, 0.01, labels["complexity"], ha="center", fontsize=9,
             color="gray", style="italic")

    plt.tight_layout(rect=[0, 0.03, 1, 1])

    if args.out:
        plt.savefig(args.out, dpi=args.dpi, bbox_inches="tight")
        print(f"Graph saved to: {args.out}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
