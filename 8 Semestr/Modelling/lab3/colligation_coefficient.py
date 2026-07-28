import pandas as pd


def main() -> None:
    df = pd.read_csv("diabetes.csv")

    glucose_col = "Glucose"
    insulin_col = "Insulin"

    glucose_median = df[glucose_col].median()
    insulin_median = df[insulin_col].median()

    # A: Glucose does not exceed its median
    # B: Insulin does not exceed its median
    a = df[glucose_col] <= glucose_median
    b = df[insulin_col] <= insulin_median

    n = len(df)
    n_a = int(a.sum())
    n_b = int(b.sum())
    n_ab = int((a & b).sum())

    p_a = n_a / n
    p_b = n_b / n
    p_a_given_b = n_ab / n_b if n_b else 0.0
    k = (p_a_given_b / p_a) if p_a else 0.0

    print("Medians:")
    print(f"  {glucose_col}: {glucose_median}")
    print(f"  {insulin_col}: {insulin_median}")
    print()
    print("Events:")
    print(f"  A: {glucose_col} <= median({glucose_col})")
    print(f"  B: {insulin_col} <= median({insulin_col})")
    print()
    print("Counts:")
    print(f"  N = {n}")
    print(f"  n(A) = {n_a}")
    print(f"  n(B) = {n_b}")
    print(f"  n(A & B) = {n_ab}")
    print()
    print("Probabilities:")
    print(f"  P(A) = {p_a:.6f}")
    print(f"  P(B) = {p_b:.6f}")
    print(f"  P(A|B) = {p_a_given_b:.6f}")
    print()
    print(f"Colligation coefficient K = P(A|B) / P(A) = {k:.6f}")


if __name__ == "__main__":
    main()
