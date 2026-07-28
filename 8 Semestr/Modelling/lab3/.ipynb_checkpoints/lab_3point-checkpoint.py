#!/usr/bin/env python3
"""
lab_3point.py  —  Логическая модель (СДНФ) + проверка адекватности
=======================================================================
Pipeline:
  1. Загрузка diabetes.csv, воспроизведение K-means (K=2) из lab41.py
     → метки кластеров используем как target y (для всех 768 строк)
  2. Разбивка 50/50 на рабочую/контрольную методом сортировочного
     чередования (sorted interleaving) — без использования кластеров,
     сохраняет распределение по признакам
  3. Бинаризация признаков по медиане рабочей выборки
  4. СДНФ на рабочей (все 7 признаков) → предсказание на контрольной
     → называем это "label" (эталон для сравнения)
  5. Для каждой непустой комбинации признаков (2^7 - 1 = 127 штук):
       - строим СДНФ на рабочей
       - предсказываем на контрольной
       - сравниваем с label
  6. Вывод: какие признаки можно отцепить без потери качества
"""

import numpy as np
import pandas as pd
from itertools import combinations
from collections import defaultdict

SEP = "=" * 80
sep = "-" * 80

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ
# ═══════════════════════════════════════════════════════════════════════════════
CSVPATH = "diabetes.csv"
df = pd.read_csv(CSVPATH)

TARGET_ORIG = "Outcome"
orig_feature_cols = [c for c in df.columns if c != TARGET_ORIG]
rename_map = {col: f"k{i+1}" for i, col in enumerate(orig_feature_cols)}
rename_map[TARGET_ORIG] = "Outcome"
df = df.rename(columns=rename_map)

# k7 = DiabetesPedigreeFunction исключён (среднее |Q| Юла = 0.0786 < 0.10)
SELECTED = ["k1", "k2", "k3", "k4", "k5", "k6", "k8"]
N_FEAT = len(SELECTED)

print(SEP)
print("ШАГ 1. Загрузка данных")
print(SEP)
print(f"  Датасет: {df.shape[0]} строк, {df.shape[1]-1} признаков")
print(f"  Отобранные признаки (k7 исключён): {SELECTED}")
print(f"  k1=Pregnancies, k2=Glucose, k3=BloodPressure, k4=SkinThickness,")
print(f"  k5=Insulin,     k6=BMI,     k8=Age")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. ВОСПРОИЗВЕДЕНИЕ K-MEANS ИЗ lab41.py (K=2, seed=42, n_init=10)
# ═══════════════════════════════════════════════════════════════════════════════

X_sel = df[SELECTED].to_numpy(dtype=float)
sel_means = X_sel.mean(axis=0)
sel_stds  = X_sel.std(axis=0)
sel_stds[sel_stds == 0] = 1.0
X_scaled  = (X_sel - sel_means) / sel_stds


def _euclidean(a, b):
    d = a - b
    return float(np.sqrt(np.dot(d, d)))


def _assign(X, centers):
    labels = np.empty(X.shape[0], dtype=int)
    for i in range(X.shape[0]):
        dists = [_euclidean(X[i], centers[k]) for k in range(len(centers))]
        labels[i] = int(np.argmin(dists))
    return labels


def _centers(X, labels, k):
    c = np.zeros((k, X.shape[1]))
    for j in range(k):
        m = labels == j
        if m.any():
            c[j] = X[m].mean(axis=0)
    return c


def _wcss(X, labels, centers):
    return sum(_euclidean(X[i], centers[labels[i]]) ** 2
               for i in range(X.shape[0]))


def _kmeans_run(X, k, max_iter, rng):
    idx = rng.choice(X.shape[0], size=k, replace=False)
    centers = X[idx].copy()
    labels  = np.full(X.shape[0], -1, dtype=int)
    for _ in range(max_iter):
        new_lbl = _assign(X, centers)
        if np.array_equal(new_lbl, labels):
            break
        labels  = new_lbl
        centers = _centers(X, labels, k)
    return labels, centers, _wcss(X, labels, centers)


def kmeans(X, k, n_init=10, max_iter=300, seed=42):
    best_lbl, best_ctr, best_w = None, None, np.inf
    rng_master = np.random.default_rng(seed)
    for _ in range(n_init):
        rng = np.random.default_rng(rng_master.integers(0, 10**9))
        lbl, ctr, w = _kmeans_run(X, k, max_iter, rng)
        if w < best_w:
            best_lbl, best_ctr, best_w = lbl.copy(), ctr.copy(), w
    return best_lbl, best_ctr, best_w


print()
print(SEP)
print("ШАГ 2. K-means (воспроизведение из lab41.py, K=2, seed=42)")
print(SEP)

K = 2
y_full, centers_full, wcss_full = kmeans(X_scaled, k=K, n_init=10, seed=42)

counts = np.bincount(y_full)
print(f"  WCSS = {wcss_full:.2f}")
for cl in range(K):
    print(f"  Кластер {cl}: {counts[cl]} строк ({counts[cl]/len(y_full)*100:.1f}%)")

# Target — метки кластеров для всего датасета
y = y_full   # shape (768,)

# ═══════════════════════════════════════════════════════════════════════════════
# 3. РАЗБИВКА 50/50: SORTED INTERLEAVING (без использования кластеров)
#
#    Метод: сортируем строки по сумме z-оценок признаков (composite score),
#    затем чередуем: чётные индексы → рабочая, нечётные → контрольная.
#    Это "сначала маленькие, потом большие" — сохраняет распределение.
# ═══════════════════════════════════════════════════════════════════════════════

composite   = X_scaled.sum(axis=1)      # суммарный z-score по всем 7 признакам
sorted_idx  = np.argsort(composite)

work_idx = sorted_idx[::2]   # чётные позиции: 0, 2, 4, …  (≈384 строки)
ctrl_idx = sorted_idx[1::2]  # нечётные:       1, 3, 5, …  (≈384 строки)

print()
print(SEP)
print("ШАГ 3. Разбивка 50/50 (sorted interleaving по composite z-score)")
print(SEP)
print(f"  Рабочая выборка:     {len(work_idx)} строк")
print(f"  Контрольная выборка: {len(ctrl_idx)} строк")
print()
print(f"  {'Признак':<6}  {'Рабочая (mean)':<18}  {'Контрольная (mean)':<18}  Δ")
for i, feat in enumerate(SELECTED):
    w_m = X_sel[work_idx, i].mean()
    c_m = X_sel[ctrl_idx, i].mean()
    print(f"  {feat:<6}  {w_m:>16.3f}  {c_m:>18.3f}  {abs(w_m-c_m):.3f}")

# Распределение target по выборкам
y_work = y[work_idx]
y_ctrl = y[ctrl_idx]
print()
print(f"  Target (кластеры) — рабочая:     "
      f"0={( y_work==0).sum()}, 1={(y_work==1).sum()}")
print(f"  Target (кластеры) — контрольная: "
      f"0={(y_ctrl==0).sum()}, 1={(y_ctrl==1).sum()}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. БИНАРИЗАЦИЯ ПРИЗНАКОВ (по медиане рабочей выборки)
# ═══════════════════════════════════════════════════════════════════════════════

work_vals = X_sel[work_idx]
medians   = np.median(work_vals, axis=0)  # медиана по рабочей

X_bin_all  = (X_sel > medians).astype(int)   # (768, 7)
X_bin_work = X_bin_all[work_idx]              # (384, 7)
X_bin_ctrl = X_bin_all[ctrl_idx]              # (384, 7)

print()
print(SEP)
print("ШАГ 4. Бинаризация (порог = медиана рабочей выборки)")
print(SEP)
print(f"  {'Признак':<6}  {'Медиана (рабочая)':<20}  "
      f"{'≤ порога (work)':<18}  {'> порога (work)'}")
for i, feat in enumerate(SELECTED):
    ones  = X_bin_work[:, i].sum()
    zeros = len(X_bin_work) - ones
    print(f"  {feat:<6}  {medians[i]:>18.3f}  {zeros:>16}  {ones:>16}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. ПОСТРОЕНИЕ СДНФ (lookup-таблица)
#
#    СДНФ строится как словарь: бинарный вектор → класс (мажоритарное голосование)
#    Для каждой уникальной комбинации бинарных признаков в рабочей выборке
#    берём класс, который встречается чаще всего среди соответствующих строк.
#    Непокрытые векторы → majority_class (класс большинства рабочей выборки).
# ═══════════════════════════════════════════════════════════════════════════════

def build_sdnf(X_bin, y, feat_mask=None):
    """
    Строит СДНФ-таблицу: tuple(бинарный вектор) → предсказанный класс.
    feat_mask: список индексов столбцов (None = все столбцы).
    Возвращает: (lookup dict, default_class для незнакомых векторов)
    """
    if feat_mask is not None:
        X_bin = X_bin[:, feat_mask]

    groups = defaultdict(list)
    for row, lbl in zip(X_bin, y):
        groups[tuple(row)].append(int(lbl))

    lookup = {vec: (1 if sum(lbls) > len(lbls) / 2 else 0)
              for vec, lbls in groups.items()}

    # Default для неизвестных векторов = класс большинства в рабочей
    default_class = 1 if y.mean() >= 0.5 else 0
    return lookup, default_class


def apply_sdnf(X_bin, lookup, default_class, feat_mask=None):
    """Применяет СДНФ-таблицу к бинарной матрице признаков."""
    if feat_mask is not None:
        X_bin = X_bin[:, feat_mask]
    return np.array([lookup.get(tuple(row), default_class) for row in X_bin])


def sdnf_description(lookup):
    """
    Возвращает строковое представление СДНФ (перечень минтермов).
    """
    minterms = sorted(vec for vec, cls in lookup.items() if cls == 1)
    maxterms = sorted(vec for vec, cls in lookup.items() if cls == 0)
    return minterms, maxterms


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ПОЛНАЯ МОДЕЛЬ (все 7 признаков) → получаем "label"
# ═══════════════════════════════════════════════════════════════════════════════

print()
print(SEP)
print("ШАГ 5. Полная СДНФ (все 7 признаков) → эталон 'label'")
print(SEP)

full_lookup, full_default = build_sdnf(X_bin_work, y_work)
minterms_full, maxterms_full = sdnf_description(full_lookup)

print(f"  Возможных бинарных векторов: 2^{N_FEAT} = {2**N_FEAT}")
print(f"  Покрыто в рабочей выборке:   {len(full_lookup)}")
print(f"  Минтермов (y=1):             {len(minterms_full)}")
print(f"  Макстермов (y=0):            {len(maxterms_full)}")
print(f"  Default для новых векторов:  {full_default}")

# Применяем к контрольной → это "label"
label = apply_sdnf(X_bin_ctrl, full_lookup, full_default)

# Проверка согласованности label vs y_ctrl (справочно)
acc_full_vs_true = (label == y_ctrl).mean()
print()
print(f"  Предсказания full СДНФ на контрольной:")
print(f"    0 → {(label==0).sum()}, 1 → {(label==1).sum()}")
print(f"  Совпадение с истинными метками кластеров K-means: "
      f"{acc_full_vs_true:.4f} ({acc_full_vs_true*100:.1f}%)")
print()
print("  Это 'label' — эталон для сравнения всех упрощённых моделей.")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. ПЕРЕБОР ВСЕХ НЕПУСТЫХ ПОДМНОЖЕСТВ ПРИЗНАКОВ (2^7 - 1 = 127)
# ═══════════════════════════════════════════════════════════════════════════════

print()
print(SEP)
print(f"ШАГ 6. СДНФ для всех непустых подмножеств признаков "
      f"(2^{N_FEAT} - 1 = {2**N_FEAT - 1} вариантов)")
print(SEP)

results = []
for r in range(1, N_FEAT + 1):
    for subset in combinations(range(N_FEAT), r):
        feat_names = [SELECTED[i] for i in subset]
        mask       = list(subset)

        lookup_sub, default_sub = build_sdnf(X_bin_work, y_work, feat_mask=mask)
        preds = apply_sdnf(X_bin_ctrl, lookup_sub, default_sub, feat_mask=mask)

        acc_vs_label = (preds == label).mean()      # совпадение с эталоном
        acc_vs_true  = (preds == y_ctrl).mean()     # совпадение с K-means

        # Покрытие: доля контрольных векторов, найденных в lookup
        X_sub_ctrl = X_bin_ctrl[:, mask]
        coverage = sum(1 for row in X_sub_ctrl
                       if tuple(row) in lookup_sub) / len(X_sub_ctrl)

        mnt = sum(1 for v in lookup_sub.values() if v == 1)
        mxt = sum(1 for v in lookup_sub.values() if v == 0)

        results.append({
            "n":            r,
            "features":     "+".join(feat_names),
            "mask":         mask,
            "acc_vs_label": acc_vs_label,
            "acc_vs_true":  acc_vs_true,
            "n_minterms":   mnt,
            "n_maxterms":   mxt,
            "lookup_size":  len(lookup_sub),
            "possible":     2 ** r,
            "coverage":     coverage,
        })

results_df = pd.DataFrame(results)
results_df.sort_values(["n", "acc_vs_label"], ascending=[True, False],
                       inplace=True)

print(f"  Готово. Оценено {len(results_df)} подмножеств.")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. ВЫВОД РЕЗУЛЬТАТОВ
# ═══════════════════════════════════════════════════════════════════════════════

THRESHOLD = 0.95   # порог "адекватности" модели

print()
print(SEP)
print("РЕЗУЛЬТАТЫ: совпадение с эталоном 'label' для каждого подмножества")
print(f"  acc_vs_label = совпадение с предсказаниями full-СДНФ на контроле")
print(f"  acc_vs_true  = совпадение с истинными метками K-means на контроле")
print(f"  Порог адекватности: acc_vs_label >= {THRESHOLD:.2f}")
print(SEP)

for r in range(1, N_FEAT + 1):
    sub = results_df[results_df["n"] == r]
    best = sub.iloc[0]
    print(f"\n─── {r} признак(ов) "
          f"(лучший: {best['features']}, "
          f"acc_vs_label={best['acc_vs_label']:.4f}) ───")
    for _, row in sub.iterrows():
        mark = "✓" if row["acc_vs_label"] >= THRESHOLD else " "
        print(f"  [{mark}] {row['features']:<38}  "
              f"vs_label={row['acc_vs_label']:.4f}  "
              f"vs_true={row['acc_vs_true']:.4f}  "
              f"minterms={row['n_minterms']:3d}  "
              f"coverage={row['coverage']:.3f}")

# ─── Итог: минимальное адекватное подмножество ───
print()
print(SEP)
print("ИТОГ: МИНИМАЛЬНЫЕ ПОДМНОЖЕСТВА С acc_vs_label >= {:.2f}".format(THRESHOLD))
print(SEP)

adequate = results_df[results_df["acc_vs_label"] >= THRESHOLD]
if len(adequate) == 0:
    print("  Ни одно подмножество не достигло порога.")
    print("  Рекомендация: снизить порог или проверить данные.")
else:
    min_n = adequate["n"].min()
    print(f"  Минимальное количество признаков: {min_n}")
    print(f"  Подмножества:")
    for _, row in adequate[adequate["n"] == min_n].iterrows():
        print(f"    {row['features']:<38}  "
              f"acc_vs_label={row['acc_vs_label']:.4f}  "
              f"acc_vs_true={row['acc_vs_true']:.4f}")

# Полная модель для справки
full_row = results_df[results_df["n"] == N_FEAT].iloc[0]
print()
print(f"  Полная модель ({N_FEAT} признаков):  "
      f"acc_vs_label={full_row['acc_vs_label']:.4f}  "
      f"acc_vs_true={full_row['acc_vs_true']:.4f}")

print()
print(SEP)
print("ОЦЕНКА АДЕКВАТНОСТИ МОДЕЛИ")
print(SEP)
if acc_full_vs_true >= 0.80:
    verdict = "АДЕКВАТНА"
    comment = f"Полная СДНФ совпадает с кластеризацией на {acc_full_vs_true*100:.1f}%"
else:
    verdict = "ТРЕБУЕТ ДОРАБОТКИ"
    comment = f"Совпадение с кластеризацией только {acc_full_vs_true*100:.1f}%"

print(f"  Вердикт: {verdict}")
print(f"  {comment}")
print(f"  Логика: если СДНФ, обученная на рабочей выборке,")
print(f"  корректно предсказывает метки на контрольной — модель обобщается.")

# ─── Сохранение результатов ───
results_df.drop(columns=["mask"]).to_csv("sdnf_results.csv", index=False)
print()
print(f"  Полные результаты сохранены → sdnf_results.csv")
print(SEP)
