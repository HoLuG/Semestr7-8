import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt





DATA_PATH = "diabetes.csv"
OUTPUT_DIR = "final_logic_model"

FEATURE_COLS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]
TARGET_COL = "Outcome"

K_CLUSTERS = 2
MAX_ITER = 100
TOL = 1e-4
RANDOM_STATE = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)





df = pd.read_csv(DATA_PATH)

X_df = df[FEATURE_COLS].copy()
y = df[TARGET_COL].astype(int).values

for col in FEATURE_COLS:
    X_df[col] = X_df[col].fillna(X_df[col].mean())

print("Размер датасета:", df.shape)
print("Используемые признаки:", FEATURE_COLS)





means = X_df.mean()

binary_df = pd.DataFrame(index=X_df.index)
for col in FEATURE_COLS:
    binary_df[col] = (X_df[col] <= means[col]).astype(int)

means.to_csv(
    os.path.join(OUTPUT_DIR, "feature_means.csv"),
    encoding="utf-8-sig",
    header=["mean"]
)









def build_2x2(x_bin, y_bin):
    a = int(((x_bin == 1) & (y_bin == 1)).sum())
    b = int(((x_bin == 1) & (y_bin == 0)).sum())
    c = int(((x_bin == 0) & (y_bin == 1)).sum())
    d = int(((x_bin == 0) & (y_bin == 0)).sum())
    return a, b, c, d


def pearson_contingency(a, b, c, d):
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    if denom == 0:
        return np.nan
    return (a * d - b * c) / denom


def yule_association(a, b, c, d):
    denom = a * d + b * c
    if denom == 0:
        return np.nan
    return (a * d - b * c) / denom


def yule_colligation(a, b, c, d):
    ad = a * d
    bc = b * c
    root_ad = math.sqrt(ad)
    root_bc = math.sqrt(bc)
    denom = root_ad + root_bc
    if denom == 0:
        return np.nan
    return (root_ad - root_bc) / denom


def bernstein_coefficient(x_bin, y_bin):
    """
    K_B = ( P(A∩B) - P(A)P(B) ) / ( P(A)(1-P(A)) )
    где:
    A = (x_bin == 1)
    B = (y_bin == 1)
    """
    pA = float((x_bin == 1).mean())
    pB = float((y_bin == 1).mean())
    pAB = float(((x_bin == 1) & (y_bin == 1)).mean())

    denom = pA * (1.0 - pA)
    if denom == 0:
        return np.nan
    return (pAB - pA * pB) / denom





n = len(FEATURE_COLS)

bernstein_matrix = pd.DataFrame(np.zeros((n, n)), index=FEATURE_COLS, columns=FEATURE_COLS)
pearson_matrix = pd.DataFrame(np.zeros((n, n)), index=FEATURE_COLS, columns=FEATURE_COLS)
yule_assoc_matrix = pd.DataFrame(np.zeros((n, n)), index=FEATURE_COLS, columns=FEATURE_COLS)
yule_coll_matrix = pd.DataFrame(np.zeros((n, n)), index=FEATURE_COLS, columns=FEATURE_COLS)

for col_i in FEATURE_COLS:
    for col_j in FEATURE_COLS:
        x_bin = binary_df[col_i]
        y_bin = binary_df[col_j]

        a, b, c, d = build_2x2(x_bin, y_bin)

        bernstein_matrix.loc[col_i, col_j] = bernstein_coefficient(x_bin, y_bin)
        pearson_matrix.loc[col_i, col_j] = pearson_contingency(a, b, c, d)
        yule_assoc_matrix.loc[col_i, col_j] = yule_association(a, b, c, d)
        yule_coll_matrix.loc[col_i, col_j] = yule_colligation(a, b, c, d)

bernstein_matrix.to_csv(os.path.join(OUTPUT_DIR, "bernstein_coefficient.csv"), encoding="utf-8-sig")
pearson_matrix.to_csv(os.path.join(OUTPUT_DIR, "pearson_contingency.csv"), encoding="utf-8-sig")
yule_assoc_matrix.to_csv(os.path.join(OUTPUT_DIR, "yule_association.csv"), encoding="utf-8-sig")
yule_coll_matrix.to_csv(os.path.join(OUTPUT_DIR, "yule_colligation.csv"), encoding="utf-8-sig")





def plot_heatmap(matrix, title, filename, vmin=-1.0, vmax=1.0):
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix.values, cmap="RdYlGn", vmin=vmin, vmax=vmax)

    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
    ax.set_yticklabels(matrix.index)
    ax.set_title(title, fontsize=17, fontweight="bold")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j, i,
                f"{matrix.iloc[i, j]:.3f}",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="black"
            )

    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=200, bbox_inches="tight")
    plt.close()


plot_heatmap(bernstein_matrix, "Коэффициент Бернштейна", "01_bernstein_coefficient.png")
plot_heatmap(pearson_matrix, "Контингенция Пирсона", "02_pearson_contingency.png")
plot_heatmap(yule_assoc_matrix, "Ассоциация Юла", "03_yule_association.png")
plot_heatmap(yule_coll_matrix, "Коллигация Юла", "04_yule_colligation.png")





def upper_triangle_values(matrix):
    vals = []
    pairs = []
    for i in range(len(matrix.index)):
        for j in range(i + 1, len(matrix.columns)):
            pairs.append((matrix.index[i], matrix.columns[j]))
            vals.append(matrix.iloc[i, j])
    return pairs, np.array(vals, dtype=float)


bernstein_sym = (bernstein_matrix + bernstein_matrix.T) / 2.0

compare_matrices = {
    "bernstein_avg": bernstein_sym,
    "pearson": pearson_matrix,
    "yule_association": yule_assoc_matrix,
    "yule_colligation": yule_coll_matrix,
}

pairs_ref = None
vectors = {}

for name, mat in compare_matrices.items():
    pairs, vals = upper_triangle_values(mat)
    if pairs_ref is None:
        pairs_ref = pairs
    vectors[name] = vals

pair_rows = []
for f1, f2 in pairs_ref:
    pair_rows.append({
        "feature_1": f1,
        "feature_2": f2,
        "bernstein_12": bernstein_matrix.loc[f1, f2],
        "bernstein_21": bernstein_matrix.loc[f2, f1],
        "bernstein_avg": bernstein_sym.loc[f1, f2],
        "pearson": pearson_matrix.loc[f1, f2],
        "yule_association": yule_assoc_matrix.loc[f1, f2],
        "yule_colligation": yule_coll_matrix.loc[f1, f2],
        "abs_bernstein_avg": abs(bernstein_sym.loc[f1, f2]),
        "abs_pearson": abs(pearson_matrix.loc[f1, f2]),
        "abs_yule_association": abs(yule_assoc_matrix.loc[f1, f2]),
        "abs_yule_colligation": abs(yule_coll_matrix.loc[f1, f2]),
    })

pair_summary_df = pd.DataFrame(pair_rows)
pair_summary_df.to_csv(
    os.path.join(OUTPUT_DIR, "pairwise_coefficients_summary.csv"),
    index=False,
    encoding="utf-8-sig"
)

metric_names = list(compare_matrices.keys())
similarity = pd.DataFrame(index=metric_names, columns=metric_names, dtype=float)
sign_agreement = pd.DataFrame(index=metric_names, columns=metric_names, dtype=float)
mean_abs_gap = pd.DataFrame(index=metric_names, columns=metric_names, dtype=float)

for m1 in metric_names:
    for m2 in metric_names:
        v1 = vectors[m1]
        v2 = vectors[m2]

        if np.std(v1) == 0 or np.std(v2) == 0:
            similarity.loc[m1, m2] = np.nan
        else:
            similarity.loc[m1, m2] = np.corrcoef(v1, v2)[0, 1]

        sign_agreement.loc[m1, m2] = np.mean(np.sign(v1) == np.sign(v2))
        mean_abs_gap.loc[m1, m2] = np.mean(np.abs(v1 - v2))

similarity.to_csv(os.path.join(OUTPUT_DIR, "coefficient_similarity_correlation.csv"), encoding="utf-8-sig")
sign_agreement.to_csv(os.path.join(OUTPUT_DIR, "coefficient_sign_agreement.csv"), encoding="utf-8-sig")
mean_abs_gap.to_csv(os.path.join(OUTPUT_DIR, "coefficient_mean_abs_gap.csv"), encoding="utf-8-sig")

plot_heatmap(similarity, "Корреляция профилей коэффициентов", "05_metric_similarity.png", vmin=-1.0, vmax=1.0)
plot_heatmap(sign_agreement, "Совпадение знаков коэффициентов", "06_metric_sign_agreement.png", vmin=0.0, vmax=1.0)

agreement_rows = []
for name in metric_names:
    others = [m for m in metric_names if m != name]
    avg_corr = float(similarity.loc[name, others].mean())
    avg_sign = float(sign_agreement.loc[name, others].mean())
    avg_gap = float(mean_abs_gap.loc[name, others].mean())
    combined_score = avg_corr + avg_sign - avg_gap

    agreement_rows.append({
        "metric": name,
        "avg_corr_with_others": avg_corr,
        "avg_sign_agreement_with_others": avg_sign,
        "avg_mean_abs_gap_with_others": avg_gap,
        "combined_score": combined_score
    })

agreement_df = pd.DataFrame(agreement_rows).sort_values("combined_score", ascending=False)
agreement_df.to_csv(
    os.path.join(OUTPUT_DIR, "metric_agreement_ranking.csv"),
    index=False,
    encoding="utf-8-sig"
)

chosen_metric_name = agreement_df.iloc[0]["metric"]
chosen_metric_matrix = compare_matrices[chosen_metric_name]

print("\nРанжирование коэффициентов по согласованности:")
print(agreement_df)
print(f"\nВыбран коэффициент для сокращения размерности: {chosen_metric_name}")





def similarity_to_distance(metric_matrix):
    """
    Объединяем признаки только по положительной связи:
        similarity = max(K, 0)
        distance = 1 - similarity
    """
    sim = metric_matrix.copy()
    sim = sim.clip(lower=0.0, upper=1.0)

    dist = (1.0 - sim).copy()
    for i in range(dist.shape[0]):
        dist.iat[i, i] = 0.0

    return dist


feature_distance_matrix = similarity_to_distance(chosen_metric_matrix)
feature_distance_matrix.to_csv(
    os.path.join(OUTPUT_DIR, "feature_distance_matrix.csv"),
    encoding="utf-8-sig"
)


def average_linkage_distance(cluster_a, cluster_b, dist_matrix):
    vals = []
    for fa in cluster_a:
        for fb in cluster_b:
            vals.append(dist_matrix.loc[fa, fb])
    return float(np.mean(vals))


def hierarchical_clustering_features(dist_matrix, feature_order):
    clusters = [[f] for f in feature_order]
    history = []

    while len(clusters) > 1:
        best_i = None
        best_j = None
        best_dist = float("inf")

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = average_linkage_distance(clusters[i], clusters[j], dist_matrix)
                if d < best_dist:
                    best_dist = d
                    best_i = i
                    best_j = j

        c1 = clusters[best_i][:]
        c2 = clusters[best_j][:]
        merged = c1 + c2

        history.append({
            "step": len(history) + 1,
            "cluster_1": ", ".join(c1),
            "cluster_2": ", ".join(c2),
            "merge_distance": best_dist,
            "clusters_count_after_merge": len(clusters) - 1
        })

        new_clusters = []
        for idx, cl in enumerate(clusters):
            if idx not in (best_i, best_j):
                new_clusters.append(cl)
        new_clusters.append(merged)
        clusters = new_clusters

    return pd.DataFrame(history)


merge_history_df = hierarchical_clustering_features(feature_distance_matrix, FEATURE_COLS)
merge_history_df.to_csv(
    os.path.join(OUTPUT_DIR, "feature_merge_history.csv"),
    index=False,
    encoding="utf-8-sig"
)

print("\nИстория слияний признаков:")
print(merge_history_df)

merge_distances = merge_history_df["merge_distance"].values

if len(merge_distances) >= 2:
    gaps = np.diff(merge_distances)
    gap_idx = int(np.argmax(gaps))
    merges_before_cut = gap_idx + 1
    n_feature_groups = max(2, len(FEATURE_COLS) - merges_before_cut)
else:
    n_feature_groups = max(2, len(FEATURE_COLS) - 1)


n_feature_groups = min(n_feature_groups, len(FEATURE_COLS) - 1)

print(f"\nЧисло групп признаков после сокращения размерности: {n_feature_groups}")


def clusters_after_n_groups(dist_matrix, feature_order, n_groups):
    clusters = [[f] for f in feature_order]

    while len(clusters) > n_groups:
        best_i = None
        best_j = None
        best_dist = float("inf")

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = average_linkage_distance(clusters[i], clusters[j], dist_matrix)
                if d < best_dist:
                    best_dist = d
                    best_i = i
                    best_j = j

        merged = clusters[best_i] + clusters[best_j]

        new_clusters = []
        for idx, cl in enumerate(clusters):
            if idx not in (best_i, best_j):
                new_clusters.append(cl)
        new_clusters.append(merged)
        clusters = new_clusters

    return clusters


feature_groups = clusters_after_n_groups(feature_distance_matrix, FEATURE_COLS, n_feature_groups)






X_std_source = X_df.copy()
source_mean = X_std_source.mean(axis=0)
source_std = X_std_source.std(axis=0)
source_std[source_std == 0] = 1.0
X_std_source = (X_std_source - source_mean) / source_std

aggregated_df = pd.DataFrame(index=X_df.index)
group_rows = []

for idx, group in enumerate(feature_groups, start=1):
    group_sorted = [f for f in FEATURE_COLS if f in group]

    if len(group_sorted) == 1:
        new_feature_name = group_sorted[0]
        aggregated_df[new_feature_name] = X_df[group_sorted[0]].values
    else:
        new_feature_name = "Agg_" + "_".join(group_sorted)
        aggregated_df[new_feature_name] = X_std_source[group_sorted].mean(axis=1)

    group_rows.append({
        "group_id": idx,
        "group_features": ", ".join(group_sorted),
        "new_feature_name": new_feature_name,
        "group_size": len(group_sorted),
        "aggregation_type": "original" if len(group_sorted) == 1 else "mean_of_standardized_features"
    })

feature_groups_df = pd.DataFrame(group_rows)
feature_groups_df.to_csv(
    os.path.join(OUTPUT_DIR, "feature_groups_and_aggregated_features.csv"),
    index=False,
    encoding="utf-8-sig"
)

selected_features = list(aggregated_df.columns)

pd.DataFrame({"selected_feature": selected_features}).to_csv(
    os.path.join(OUTPUT_DIR, "selected_features_after_reduction.csv"),
    index=False,
    encoding="utf-8-sig"
)

print("\nГруппы признаков и новые агрегированные признаки:")
print(feature_groups_df)
print("\nИтоговый набор признаков после сокращения размерности:")
print(selected_features)

plt.figure(figsize=(8, 5))
plt.plot(range(1, len(merge_distances) + 1), merge_distances, marker="o")
plt.xlabel("Шаг слияния")
plt.ylabel("Расстояние слияния")
plt.title("Иерархическое объединение признаков")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "07_feature_merge_distances.png"), dpi=200)
plt.close()





X = aggregated_df.values.astype(float)

mean = X.mean(axis=0)
std = X.std(axis=0)
std[std == 0] = 1.0
X_scaled = (X - mean) / std


def euclidean_distances(X, centers):
    return np.sqrt(((X[:, np.newaxis, :] - centers[np.newaxis, :, :]) ** 2).sum(axis=2))


def initialize_centers_kmeans_pp(X, k, random_state=42):
    rng = np.random.default_rng(random_state)
    n_samples = X.shape[0]

    centers = []
    first_idx = rng.integers(0, n_samples)
    centers.append(X[first_idx].copy())

    for _ in range(1, k):
        centers_array = np.array(centers)
        dist_sq = ((X[:, np.newaxis, :] - centers_array[np.newaxis, :, :]) ** 2).sum(axis=2)
        min_dist_sq = np.min(dist_sq, axis=1)

        total = min_dist_sq.sum()
        if total == 0:
            next_idx = rng.integers(0, n_samples)
        else:
            probs = min_dist_sq / total
            next_idx = rng.choice(n_samples, p=probs)

        centers.append(X[next_idx].copy())

    return np.array(centers)


def assign_clusters(X, centers):
    distances = euclidean_distances(X, centers)
    return np.argmin(distances, axis=1)


def recompute_centers(X, labels, k, old_centers):
    new_centers = []
    for cluster_id in range(k):
        cluster_points = X[labels == cluster_id]
        if len(cluster_points) == 0:
            new_centers.append(old_centers[cluster_id])
        else:
            new_centers.append(cluster_points.mean(axis=0))
    return np.array(new_centers)


def compute_inertia(X, labels, centers):
    total = 0.0
    for cluster_id in range(len(centers)):
        cluster_points = X[labels == cluster_id]
        if len(cluster_points) > 0:
            total += ((cluster_points - centers[cluster_id]) ** 2).sum()
    return total


def kmeans(X, k=2, max_iter=100, tol=1e-4, random_state=42):
    centers = initialize_centers_kmeans_pp(X, k, random_state=random_state)

    history_inertia = []
    history_shift = []

    for iteration in range(max_iter):
        labels = assign_clusters(X, centers)
        new_centers = recompute_centers(X, labels, k, centers)

        shift = np.sqrt(((new_centers - centers) ** 2).sum(axis=1)).max()
        inertia = compute_inertia(X, labels, new_centers)

        history_inertia.append(inertia)
        history_shift.append(shift)

        print(
            f"Итерация {iteration + 1:2d}: "
            f"inertia = {inertia:.6f}, "
            f"max_shift = {shift:.6f}"
        )

        centers = new_centers

        if shift < tol:
            print("Центры стабилизировались. Остановка.")
            break

    labels = assign_clusters(X, centers)
    final_inertia = compute_inertia(X, labels, centers)

    return labels, centers, history_inertia, history_shift, final_inertia


labels_raw, centers_scaled, history_inertia, history_shift, final_inertia = kmeans(
    X_scaled,
    k=K_CLUSTERS,
    max_iter=MAX_ITER,
    tol=TOL,
    random_state=RANDOM_STATE
)

print(f"\nФинальная inertia: {final_inertia:.6f}")





error_direct = np.mean(labels_raw != y)
error_inverted = np.mean((1 - labels_raw) != y)

if error_inverted < error_direct:
    labels = 1 - labels_raw
    chosen_error = error_inverted
    print("\nДля сравнения с Outcome метки кластеров инвертированы.")
else:
    labels = labels_raw
    chosen_error = error_direct
    print("\nМетки кластеров оставлены как есть.")

accuracy = 1.0 - chosen_error

print(f"Ошибка относительно Outcome: {chosen_error:.6f}")
print(f"Точность относительно Outcome: {accuracy:.6f}")





result_df = pd.DataFrame({
    "Outcome": y,
    "Cluster": labels
})
result_df.to_csv(
    os.path.join(OUTPUT_DIR, "outcome_vs_cluster.csv"),
    index=False,
    encoding="utf-8-sig"
)

centers_df = pd.DataFrame(centers_scaled, columns=selected_features)
centers_df.index = [f"Cluster_{i}" for i in range(K_CLUSTERS)]
centers_df.to_csv(
    os.path.join(OUTPUT_DIR, "cluster_centers_scaled_aggregated_features.csv"),
    encoding="utf-8-sig"
)

tn = np.sum((y == 0) & (labels == 0))
fp = np.sum((y == 0) & (labels == 1))
fn = np.sum((y == 1) & (labels == 0))
tp = np.sum((y == 1) & (labels == 1))

conf_matrix = np.array([
    [tn, fp],
    [fn, tp]
])

pd.DataFrame(
    conf_matrix,
    index=["Outcome_0", "Outcome_1"],
    columns=["Cluster_0", "Cluster_1"]
).to_csv(
    os.path.join(OUTPUT_DIR, "confusion_matrix.csv"),
    encoding="utf-8-sig"
)





plt.figure(figsize=(8, 5))
plt.plot(range(1, len(history_inertia) + 1), history_inertia, marker="o")
plt.xlabel("Итерация")
plt.ylabel("Inertia")
plt.title("Сходимость k-means")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "08_kmeans_convergence.png"), dpi=200)
plt.close()

plt.figure(figsize=(8, 5))
plt.plot(range(1, len(history_shift) + 1), history_shift, marker="o")
plt.xlabel("Итерация")
plt.ylabel("Максимальный сдвиг центров")
plt.title("Стабилизация центров")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "09_kmeans_center_shift.png"), dpi=200)
plt.close()


def pca_2d(X):
    X_centered = X - X.mean(axis=0)
    cov = np.cov(X_centered, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    components = eigenvectors[:, :2]
    X_proj = X_centered @ components
    return X_proj, components, eigenvalues


if X_scaled.shape[1] == 2:
    plt.figure(figsize=(8, 6))
    for cluster_id in range(K_CLUSTERS):
        mask = labels == cluster_id
        plt.scatter(
            X_scaled[mask, 0],
            X_scaled[mask, 1],
            alpha=0.6,
            label=f"Кластер {cluster_id}"
        )

    plt.scatter(
        centers_scaled[:, 0],
        centers_scaled[:, 1],
        marker="X",
        s=250,
        linewidths=2,
        label="Центры"
    )

    plt.xlabel(selected_features[0])
    plt.ylabel(selected_features[1])
    plt.title("Кластеры в пространстве сокращённых признаков")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "10_clusters_2d.png"), dpi=200)
    plt.close()
else:
    X_pca, pca_components, pca_eigenvalues = pca_2d(X_scaled)
    centers_pca = (centers_scaled - X_scaled.mean(axis=0)) @ pca_components

    pca_loadings_df = pd.DataFrame(
        pca_components,
        index=selected_features,
        columns=["PC1", "PC2"]
    )
    pca_loadings_df.to_csv(
        os.path.join(OUTPUT_DIR, "pca_loadings_aggregated_features.csv"),
        encoding="utf-8-sig"
    )

    plt.figure(figsize=(8, 6))
    for cluster_id in range(K_CLUSTERS):
        mask = labels == cluster_id
        plt.scatter(
            X_pca[mask, 0],
            X_pca[mask, 1],
            alpha=0.6,
            label=f"Кластер {cluster_id}"
        )

    plt.scatter(
        centers_pca[:, 0],
        centers_pca[:, 1],
        marker="X",
        s=250,
        linewidths=2,
        label="Центры"
    )

    plt.xlabel("Первая главная компонента")
    plt.ylabel("Вторая главная компонента")
    plt.title("Кластеры в PCA-проекции сокращённого пространства признаков")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "10_clusters_2d.png"), dpi=200)
    plt.close()

plt.figure(figsize=(6, 5))
plt.imshow(conf_matrix, interpolation="nearest")
plt.colorbar()
plt.xticks([0, 1], ["Cluster = 0", "Cluster = 1"])
plt.yticks([0, 1], ["Outcome = 0", "Outcome = 1"])
plt.title("Матрица ошибок")

for i in range(2):
    for j in range(2):
        plt.text(j, i, str(conf_matrix[i, j]), ha="center", va="center")

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "11_confusion_matrix.png"), dpi=200)
plt.close()





centers_scaled_df = pd.DataFrame(
    centers_scaled,
    columns=selected_features,
    index=[f"Cluster_{i}" for i in range(K_CLUSTERS)]
)

cluster_profile_df = pd.DataFrame({
    "cluster_0_center_scaled": centers_scaled_df.loc["Cluster_0"],
    "cluster_1_center_scaled": centers_scaled_df.loc["Cluster_1"],
    "difference_cluster1_minus_cluster0": centers_scaled_df.loc["Cluster_1"] - centers_scaled_df.loc["Cluster_0"]
})
cluster_profile_df["abs_difference"] = cluster_profile_df["difference_cluster1_minus_cluster0"].abs()
cluster_profile_df = cluster_profile_df.sort_values("abs_difference", ascending=False)

cluster_profile_df.to_csv(
    os.path.join(OUTPUT_DIR, "cluster_profile_differences.csv"),
    encoding="utf-8-sig"
)

plt.figure(figsize=(8, 5))
plt.bar(cluster_profile_df.index, cluster_profile_df["difference_cluster1_minus_cluster0"].values)
plt.axhline(0, color="black", linewidth=0.8)
plt.xticks(rotation=45, ha="right")
plt.ylabel("Разность центров")
plt.title("Различие кластеров по выбранным признакам")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "12_cluster_profile_differences.png"), dpi=200)
plt.close()





with open(os.path.join(OUTPUT_DIR, "report_summary.txt"), "w", encoding="utf-8") as f:
    f.write("Построение стохастической модели\n")
    f.write("================================\n")
    f.write(f"Исходные признаки: {', '.join(FEATURE_COLS)}\n")
    f.write("Бинаризация: по среднему\n")
    f.write(f"Выбранный коэффициент для сокращения размерности: {chosen_metric_name}\n")
    f.write(f"Число групп признаков после иерархического объединения: {n_feature_groups}\n")
    f.write(f"Новый набор признаков: {', '.join(selected_features)}\n")
    f.write(f"Финальная inertia: {final_inertia:.6f}\n")
    f.write(f"Ошибка относительно Outcome: {chosen_error:.6f}\n")
    f.write(f"Точность относительно Outcome: {accuracy:.6f}\n")
    f.write("\nРазличие центров кластеров:\n")
    f.write(cluster_profile_df.to_string())
    f.write("\n")





print("\n" + "=" * 72)
print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
print("=" * 72)
print("I. Бинаризация показателей выполнена по среднему.")
print("II. Построены и сравнены 4 коэффициента взаимосвязи.")
print(f"III. Для сокращения размерности выбран коэффициент: {chosen_metric_name}")
print(f"IV. Число групп признаков после иерархического объединения: {n_feature_groups}")
print(f"V. После сокращения размерности сформированы признаки: {selected_features}")
print(f"VI. K-means выполнен по {len(selected_features)} признакам, число кластеров = {K_CLUSTERS}")
print(f"VII. Число итераций до стабилизации: {len(history_inertia)}")
print(f"VIII. Финальная inertia: {final_inertia:.6f}")
print(f"IX. Внешняя ошибка относительно Outcome: {chosen_error:.6f}")
print(f"X. Внешняя точность относительно Outcome: {accuracy:.6f}")
print("=" * 72)

print("\nОсновные файлы:")
for fname in [
    "01_bernstein_coefficient.png",
    "02_pearson_contingency.png",
    "03_yule_association.png",
    "04_yule_colligation.png",
    "05_metric_similarity.png",
    "06_metric_sign_agreement.png",
    "07_feature_merge_distances.png",
    "pairwise_coefficients_summary.csv",
    "metric_agreement_ranking.csv",
    "feature_distance_matrix.csv",
    "feature_merge_history.csv",
    "feature_groups_and_aggregated_features.csv",
    "selected_features_after_reduction.csv",
    "08_kmeans_convergence.png",
    "09_kmeans_center_shift.png",
    "10_clusters_2d.png",
    "11_confusion_matrix.png",
    "12_cluster_profile_differences.png",
    "report_summary.txt",
]:
    print("-", os.path.join(OUTPUT_DIR, fname))


# ============================================================
# XI. ЛОГИЧЕСКАЯ МОДЕЛЬ (СДНФ + минимизация, разбиение 50/50)
# ============================================================

# Бинаризация итоговых признаков (после сокращения размерности)
logic_binary_df = pd.DataFrame(index=binary_df.index)

for col in selected_features:
    if col in binary_df.columns:
        logic_binary_df[col] = binary_df[col].values
    else:
        agg_vals = aggregated_df[col]
        logic_binary_df[col] = (agg_vals <= agg_vals.mean()).astype(int)

feature_names = list(selected_features)
n_features = len(feature_names)

# --- Разбиение 50/50 через вариационный ряд и чередование ---
# По методике преподавателя: сортируем по столбцу (вариационный ряд),
# затем чередованием делим на рабочую и контрольную выборки.
# Это гарантирует сохранение распределения в обеих половинах.

# Сортируем по первому агрегированному признаку (Glucose — наиболее значимый)
sort_col = selected_features[0]
sorted_indices = np.argsort(aggregated_df[sort_col].values)

# Чередование: чётные позиции -> рабочая, нечётные -> контрольная
train_idx = sorted_indices[0::2]  # 0, 2, 4, ...
test_idx = sorted_indices[1::2]   # 1, 3, 5, ...

train_binary = logic_binary_df.iloc[train_idx].reset_index(drop=True)
test_binary = logic_binary_df.iloc[test_idx].reset_index(drop=True)

train_labels = labels[train_idx]
test_labels = labels[test_idx]

# Проверка критерием Колмогорова-Смирнова: распределения не должны различаться
print(f"\n{'=' * 72}")
print("XI. ЛОГИЧЕСКАЯ МОДЕЛЬ (разбиение 50/50, вариационный ряд + чередование)")
print(f"{'=' * 72}")
print(f"Сортировка по: {sort_col}")
print(f"Рабочая выборка:     {len(train_idx)} объектов")
print(f"Контрольная выборка: {len(test_idx)} объектов")

print(f"\nПроверка Колмогорова-Смирнова (распределения рабочей и контрольной):")
ks_results = []
for col in selected_features:
    train_vals = aggregated_df[col].values[train_idx]
    test_vals = aggregated_df[col].values[test_idx]

    # Статистика Колмогорова-Смирнова вручную
    all_vals = np.sort(np.unique(np.concatenate([train_vals, test_vals])))
    d_max = 0.0
    for v in all_vals:
        f_train = np.mean(train_vals <= v)
        f_test = np.mean(test_vals <= v)
        d_max = max(d_max, abs(f_train - f_test))

    n1 = len(train_vals)
    n2 = len(test_vals)
    # Критическое значение при alpha=0.05: D_crit = 1.36 * sqrt((n1+n2)/(n1*n2))
    d_crit = 1.36 * math.sqrt((n1 + n2) / (n1 * n2))
    passed = "ОК" if d_max <= d_crit else "РАЗЛИЧАЮТСЯ"

    ks_results.append({
        "feature": col,
        "D_n": round(d_max, 4),
        "D_crit": round(d_crit, 4),
        "result": passed
    })
    print(f"  {col}: D_n={d_max:.4f}, D_crit={d_crit:.4f} -> {passed}")

ks_df = pd.DataFrame(ks_results)
ks_df.to_csv(
    os.path.join(OUTPUT_DIR, "ks_test_train_vs_test.csv"),
    index=False,
    encoding="utf-8-sig"
)

# --- Построение СДНФ на обучающей части ---
train_binary["Cluster"] = train_labels

positive_train = train_binary[train_binary["Cluster"] == 1][feature_names]
unique_minterms = positive_train.drop_duplicates().values.tolist()

print(f"\nОбучающая часть: строк с Cluster=1: {int(train_labels.sum())}")
print(f"Уникальных минтермов: {len(unique_minterms)}")


def minterm_to_str(minterm, names):
    parts = []
    for val, name in zip(minterm, names):
        if val is None:
            continue
        if val == 1:
            parts.append(name)
        else:
            parts.append(f"!{name}")
    return " & ".join(parts) if parts else "1"


sdnf_terms = [minterm_to_str(m, feature_names) for m in unique_minterms]
sdnf_formula = " V\n    ".join(f"({t})" for t in sdnf_terms)

print(f"\nСДНФ ({len(unique_minterms)} минтермов):")
print(f"    {sdnf_formula}")


# --- Минимизация методом Куайна-МакКласки ---

def minterms_can_merge(m1, m2):
    diff_pos = None
    for i in range(len(m1)):
        if m1[i] != m2[i]:
            if diff_pos is not None:
                return None
            diff_pos = i
    return diff_pos


def quine_mccluskey(minterms, n_vars):
    current = set()
    for m in minterms:
        current.add(tuple(m))

    all_prime = set()

    while current:
        used = set()
        new_implicants = set()

        current_list = sorted(
            current,
            key=lambda t: tuple((x if x is not None else -1) for x in t)
        )
        for i in range(len(current_list)):
            for j in range(i + 1, len(current_list)):
                diff_pos = minterms_can_merge(current_list[i], current_list[j])
                if diff_pos is not None:
                    merged = list(current_list[i])
                    merged[diff_pos] = None
                    new_implicants.add(tuple(merged))
                    used.add(current_list[i])
                    used.add(current_list[j])

        for impl in current:
            if impl not in used:
                all_prime.add(impl)

        current = new_implicants

    minterm_set = set(tuple(m) for m in minterms)
    prime_list = list(all_prime)

    def covers(impl, minterm):
        for k in range(len(impl)):
            if impl[k] is not None and impl[k] != minterm[k]:
                return False
        return True

    uncovered = set(minterm_set)
    selected = []

    while uncovered:
        best_impl = None
        best_count = 0
        for impl in prime_list:
            count = sum(1 for m in uncovered if covers(impl, m))
            if count > best_count:
                best_count = count
                best_impl = impl
        if best_impl is None or best_count == 0:
            break
        selected.append(best_impl)
        uncovered = {m for m in uncovered if not covers(best_impl, m)}

    return selected


minimized = quine_mccluskey(unique_minterms, n_features)

min_terms_str = [minterm_to_str(list(impl), feature_names) for impl in minimized]
min_formula = " V\n    ".join(f"({t})" for t in min_terms_str)

print(f"\nМинимизированная ДНФ ({len(minimized)} импликант):")
print(f"    {min_formula}")


# --- Применение логической модели ---

def evaluate_dnf(row, implicants, names):
    for impl in implicants:
        match = True
        for k in range(len(impl)):
            if impl[k] is not None and impl[k] != row[names[k]]:
                match = False
                break
        if match:
            return 1
    return 0


# A) Проверка на обучающей выборке
train_logic_pred = train_binary.apply(
    lambda row: evaluate_dnf(row, minimized, feature_names), axis=1
).values

train_acc = np.mean(train_logic_pred == train_labels)

print(f"\n--- Обучающая выборка (train) ---")
print(f"  Логическая модель vs кластеризация: точность = {train_acc:.4f}")
print(f"  TP={np.sum((train_logic_pred == 1) & (train_labels == 1))}, "
      f"FN={np.sum((train_logic_pred == 0) & (train_labels == 1))}, "
      f"FP={np.sum((train_logic_pred == 1) & (train_labels == 0))}, "
      f"TN={np.sum((train_logic_pred == 0) & (train_labels == 0))}")

# B) Проверка на тестовой выборке
test_logic_pred = test_binary.apply(
    lambda row: evaluate_dnf(row, minimized, feature_names), axis=1
).values

# Сравнение 1: логическая модель vs кластеризация (метки из общего k-means)
test_acc_vs_cluster = np.mean(test_logic_pred == test_labels)

test_tp = np.sum((test_logic_pred == 1) & (test_labels == 1))
test_fn = np.sum((test_logic_pred == 0) & (test_labels == 1))
test_fp = np.sum((test_logic_pred == 1) & (test_labels == 0))
test_tn = np.sum((test_logic_pred == 0) & (test_labels == 0))

print(f"\n--- Тестовая выборка (test) ---")
print(f"  Логическая модель vs кластеризация: точность = {test_acc_vs_cluster:.4f}")
print(f"  TP={test_tp}, FN={test_fn}, FP={test_fp}, TN={test_tn}")

# Сравнение 2: логическая модель vs реальный Outcome на тесте
test_y = y[test_idx]

logic_vs_outcome_acc = np.mean(test_logic_pred == test_y)
cluster_vs_outcome_acc = np.mean(test_labels == test_y)

print(f"\n--- Сравнение моделей на тестовой выборке vs Outcome ---")
print(f"  K-means (стохастическая модель):  точность = {cluster_vs_outcome_acc:.4f}")
print(f"  Логическая модель (минимиз. ДНФ): точность = {logic_vs_outcome_acc:.4f}")

# Совпадение двух моделей между собой на тесте
agreement = np.mean(test_logic_pred == test_labels)
print(f"\n  Совпадение логической и стохастической моделей на тесте: {agreement:.4f}")


# --- Сохраняем результаты ---

logic_binary_df["Cluster"] = labels
logic_binary_df.to_csv(
    os.path.join(OUTPUT_DIR, "logic_binary_table.csv"),
    index=False,
    encoding="utf-8-sig"
)

with open(os.path.join(OUTPUT_DIR, "logic_model.txt"), "w", encoding="utf-8") as f:
    f.write("ЛОГИЧЕСКАЯ МОДЕЛЬ (СДНФ и минимизация)\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Признаки: {', '.join(feature_names)}\n")
    f.write(f"Бинаризация: 1 если значение <= среднего, иначе 0\n\n")
    f.write(f"Разбиение: вариационный ряд по {sort_col} + чередование\n")
    f.write(f"  Рабочая: {len(train_idx)}, Контрольная: {len(test_idx)}\n\n")
    f.write(f"Проверка Колмогорова-Смирнова (alpha=0.05):\n")
    for _, row in ks_df.iterrows():
        f.write(f"  {row['feature']}: D_n={row['D_n']}, D_crit={row['D_crit']} -> {row['result']}\n")
    f.write("\n")

    f.write(f"ОБУЧАЮЩАЯ ЧАСТЬ:\n")
    f.write(f"  Строк с Cluster=1: {int(train_labels.sum())}\n")
    f.write(f"  Уникальных минтермов: {len(unique_minterms)}\n\n")

    f.write(f"СДНФ ({len(unique_minterms)} минтермов):\n")
    f.write(f"  {sdnf_formula}\n\n")
    f.write(f"Минимизированная ДНФ ({len(minimized)} импликант):\n")
    f.write(f"  {min_formula}\n\n")

    f.write(f"ПРОВЕРКА НА ОБУЧАЮЩЕЙ ВЫБОРКЕ:\n")
    f.write(f"  Логическая модель vs кластеризация: {train_acc:.4f}\n\n")

    f.write(f"ПРОВЕРКА НА ТЕСТОВОЙ ВЫБОРКЕ:\n")
    f.write(f"  Логическая модель vs кластеризация: {test_acc_vs_cluster:.4f}\n")
    f.write(f"  TP={test_tp}, FN={test_fn}, FP={test_fp}, TN={test_tn}\n\n")

    f.write(f"СРАВНЕНИЕ МОДЕЛЕЙ НА ТЕСТЕ vs Outcome:\n")
    f.write(f"  K-means (стохастическая):  {cluster_vs_outcome_acc:.4f}\n")
    f.write(f"  Логическая (минимиз. ДНФ): {logic_vs_outcome_acc:.4f}\n")
    f.write(f"  Совпадение моделей между собой: {agreement:.4f}\n")

print(f"\nЛогическая модель сохранена в {os.path.join(OUTPUT_DIR, 'logic_model.txt')}")