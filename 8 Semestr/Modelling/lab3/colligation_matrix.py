import pandas as pd


def main() -> None:
    df = pd.read_csv("diabetes.csv")

    # Берем все признаки, кроме целевого столбца
    feature_cols = [c for c in df.columns if c != "Outcome"]

    # Для каждого признака формируем булевы события:
    # событие признака i: значение <= медианы признака i
    events = {}
    for col in feature_cols:
        median_value = df[col].median()
        events[col] = df[col] <= median_value

    # Матрица коэффициентов K_ij = P(A_i | B_j) / P(A_i)
    k_matrix = pd.DataFrame(index=feature_cols, columns=feature_cols, dtype=float)

    n = len(df)
    for i_col in feature_cols:
        a = events[i_col]
        n_a = int(a.sum())
        p_a = n_a / n if n else 0.0

        for j_col in feature_cols:
            b = events[j_col]
            n_b = int(b.sum())
            n_ab = int((a & b).sum())

            p_a_given_b = (n_ab / n_b) if n_b else 0.0
            k_ij = (p_a_given_b / p_a) if p_a else 0.0
            k_matrix.loc[i_col, j_col] = k_ij

    # Красивый вывод
    print("Colligation coefficient matrix K_ij = P(A_i | B_j) / P(A_i)")
    print("A_i: feature_i <= median(feature_i)")
    print("B_j: feature_j <= median(feature_j)")
    print()
    print(k_matrix.round(6).to_string())

    # Сохраняем в файл
    output_file = "colligation_matrix.csv"
    k_matrix.to_csv(output_file, index=True)
    print()
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
