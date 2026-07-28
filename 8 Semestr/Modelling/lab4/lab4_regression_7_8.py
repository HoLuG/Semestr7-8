import math
from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent

RANDOM_SEED = 42
TEST_SIZE = 0.2

KS_ALPHA = 0.05

# Отбор признаков: хотим оставить k признаков, сильнее связанных с Y по Спирмену,
# но избегать сильной взаимной корреляции между выбранными.
K_KEEP = 4
MAX_PAIR_ABS_RHO = 0.60  # мягкое ограничение на избыточность (можно ослабить)


def train_test_split_idx(n: int, test_size: float, seed: int):
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    m = int(round(n * test_size))
    test = np.sort(idx[:m])
    train = np.sort(idx[m:])
    return train, test


def standardize_fit(X: np.ndarray):
    mu = X.mean(axis=0)
    sigma = X.std(axis=0, ddof=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    return mu, sigma


def standardize_apply(X: np.ndarray, mu: np.ndarray, sigma: np.ndarray):
    return (X - mu) / sigma


def mom_linear_regression(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-10):
    # β_hat = (Z^T Z)^(-1) Z^T y  (MoM / нормальные уравнения)
    Z = np.asarray(Z, float)
    y = np.asarray(y, float)
    A = Z.T @ Z
    A = A + ridge * np.eye(A.shape[0])
    b = Z.T @ y
    beta = np.linalg.solve(A, b)
    return beta


def predict(Z: np.ndarray, beta: np.ndarray):
    return Z @ beta


def mse(y, yhat):
    y = np.asarray(y, float)
    yhat = np.asarray(yhat, float)
    return float(np.mean((y - yhat) ** 2))


def mae(y, yhat):
    y = np.asarray(y, float)
    yhat = np.asarray(yhat, float)
    return float(np.mean(np.abs(y - yhat)))


def r2(y, yhat):
    y = np.asarray(y, float)
    yhat = np.asarray(yhat, float)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def ks_2sample_pvalue(x: np.ndarray, y: np.ndarray):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    n = len(x)
    m = len(y)
    if n < 3 or m < 3:
        return float("nan"), float("nan")

    try:
        from scipy.stats import ks_2samp  # type: ignore

        res = ks_2samp(x, y, alternative="two-sided", mode="auto")
        return float(res.statistic), float(res.pvalue)
    except Exception:
        x_sorted = np.sort(x)
        y_sorted = np.sort(y)
        data_all = np.sort(np.concatenate([x_sorted, y_sorted]))
        cdf_x = np.searchsorted(x_sorted, data_all, side="right") / n
        cdf_y = np.searchsorted(y_sorted, data_all, side="right") / m
        d = float(np.max(np.abs(cdf_x - cdf_y)))
        en = math.sqrt(n * m / (n + m))
        lam = (en + 0.12 + 0.11 / en) * d
        j = np.arange(1, 200)
        p = 2.0 * np.sum(((-1) ** (j - 1)) * np.exp(-2.0 * (j * j) * (lam * lam)))
        p = float(np.clip(p, 0.0, 1.0))
        return d, p


def greedy_select_strong_low_redundancy(
    feats: list[str],
    rho_y: pd.Series,
    abs_rho_xx: pd.DataFrame,
    k: int,
    max_pair_abs_rho: float,
):
    # старт: самый сильный по |rho(Y, Xj)|
    ordered = rho_y.abs().sort_values(ascending=False).index.tolist()
    selected: list[str] = []
    for f in ordered:
        if not selected:
            selected.append(f)
            if len(selected) >= k:
                break
            continue
        max_to_sel = float(abs_rho_xx.loc[f, selected].max())
        if max_to_sel <= max_pair_abs_rho:
            selected.append(f)
            if len(selected) >= k:
                break

    # если не набрали k, добираем просто по силе
    if len(selected) < k:
        for f in ordered:
            if f not in selected:
                selected.append(f)
                if len(selected) >= k:
                    break

    return selected


def main():
    df = pd.read_csv(DIR / "diabetes.csv")

    y_name = "Glucose"
    drop = {"Outcome", "Insulin"}
    x_names_all = [c for c in df.columns if c not in drop and c != y_name]

    y = df[y_name].astype(float).to_numpy()
    Xall = df[x_names_all].astype(float)

    # --- Пункт 7: отбор (сокращение) факторов ---
    rho_y = Xall.corrwith(pd.Series(y), method="spearman")
    abs_rho_xx = Xall.corr(method="spearman").abs()

    selected = greedy_select_strong_low_redundancy(
        feats=x_names_all,
        rho_y=rho_y,
        abs_rho_xx=abs_rho_xx,
        k=K_KEEP,
        max_pair_abs_rho=MAX_PAIR_ABS_RHO,
    )
    removed = [f for f in x_names_all if f not in selected]

    # --- Пункт 8: оценка качества модели ---
    n = len(df)
    tr, te = train_test_split_idx(n, TEST_SIZE, RANDOM_SEED)

    X = Xall[selected].to_numpy(float)
    Xtr, Xte = X[tr], X[te]
    ytr, yte = y[tr], y[te]

    mu, sigma = standardize_fit(Xtr)
    Xtr_s = standardize_apply(Xtr, mu, sigma)
    Xte_s = standardize_apply(Xte, mu, sigma)

    Ztr = np.column_stack([np.ones(len(tr)), Xtr_s])
    Zte = np.column_stack([np.ones(len(te)), Xte_s])

    beta = mom_linear_regression(Ztr, ytr)
    yhat_tr = predict(Ztr, beta)
    yhat_te = predict(Zte, beta)

    resid_tr = ytr - yhat_tr
    resid_te = yte - yhat_te

    # KS: сравнение распределений y_test и yhat_test (как проверка согласия по распределению)
    ks_stat_y, ks_p_y = ks_2sample_pvalue(yte, yhat_te)

    # KS: остатки vs N(0, s^2) — проверка "нормальности" (через 1-sample KS к нормальному)
    # Реализуем через нормировку и ks_2sample к сгенерированному эталону.
    rng = np.random.default_rng(RANDOM_SEED)
    s = float(np.std(resid_te, ddof=0))
    ref = rng.normal(0.0, s if s > 0 else 1.0, size=len(resid_te))
    ks_stat_e, ks_p_e = ks_2sample_pvalue(resid_te, ref)

    out_lines = []
    out_lines.append("ЛР4 — пункты 7 и 8 (конкретные результаты)\n")
    out_lines.append("Постановка: Y=Glucose, исключены Outcome и Insulin.\n")
    out_lines.append(f"Всего факторов после исключений: {len(x_names_all)}: {', '.join(x_names_all)}\n")
    out_lines.append("")

    out_lines.append("7) Сокращение числа факторов (Spearman):")
    out_lines.append("Корреляция Спирмена ρ_S(Y, Xj):")
    for name, val in rho_y.sort_values(key=lambda s: s.abs(), ascending=False).items():
        out_lines.append(f"  {name:24s}  rho_S = {float(val): .6f}")
    out_lines.append("")
    out_lines.append(f"Выбрано k={K_KEEP} признаков (сильные по |rho_S(Y,X)| + ограничение избыточности max |rho_S(Xi,Xj)| <= {MAX_PAIR_ABS_RHO}):")
    out_lines.append("  selected = " + ", ".join(selected))
    out_lines.append("  removed  = " + ", ".join(removed))
    out_lines.append("")

    out_lines.append("8) Линейная регрессия (MoM / нормальные уравнения) на стандартизованных X:")
    out_lines.append(f"Разбиение: train={len(tr)}, test={len(te)} (seed={RANDOM_SEED})")
    out_lines.append("Коэффициенты модели (на стандартизованных признаках):")
    out_lines.append(f"  β0 (intercept) = {beta[0]: .6f}")
    for j, name in enumerate(selected, start=1):
        out_lines.append(f"  β[{name:24s}] = {beta[j]: .6f}")
    out_lines.append("")
    out_lines.append("Метрики:")
    out_lines.append(f"  train: MSE={mse(ytr, yhat_tr):.6f}, MAE={mae(ytr, yhat_tr):.6f}, R^2={r2(ytr, yhat_tr):.6f}")
    out_lines.append(f"  test : MSE={mse(yte, yhat_te):.6f}, MAE={mae(yte, yhat_te):.6f}, R^2={r2(yte, yhat_te):.6f}")
    out_lines.append("")
    out_lines.append("Анализ остатков (test):")
    out_lines.append(f"  mean(residual) = {float(np.mean(resid_te)):.6f}")
    out_lines.append(f"  std(residual)  = {float(np.std(resid_te, ddof=0)):.6f}")
    out_lines.append("")
    out_lines.append("KS-проверки (α=0.05):")
    out_lines.append(f"  KS(y_test vs yhat_test): D={ks_stat_y:.6f}, p={ks_p_y:.6g}  => {'OK (не отвергаем)' if (np.isfinite(ks_p_y) and ks_p_y>=KS_ALPHA) else 'reject'}")
    out_lines.append(f"  KS(resid_test vs N(0, s^2) ref): D={ks_stat_e:.6f}, p={ks_p_e:.6g}  => {'OK (не отвергаем)' if (np.isfinite(ks_p_e) and ks_p_e>=KS_ALPHA) else 'reject'}")
    out_lines.append("")

    out_path = DIR / "reports" / "lab4_results_7_8.txt"
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("Saved:", out_path)


if __name__ == "__main__":
    main()

