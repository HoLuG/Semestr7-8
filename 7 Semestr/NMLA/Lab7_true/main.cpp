#include <iostream>
#include <vector>
#include <cmath>

#include <cblas.h>
#include <lapacke.h>

inline double &A_at(std::vector<double> &A, int ld, int i, int j) {
    return A[j * ld + i];
}
inline double A_at(const std::vector<double> &A, int ld, int i, int j) {
    return A[j * ld + i];
}

// Печать вектора
void print_vector(const std::vector<double> &v) {
    for (double x: v) {
        std::cout << x << " ";
    }
    std::cout << "\n";
}

// Печать матрицы в привычном виде (по строкам)
void print_matrix(const std::vector<double> &M, int rows, int cols) {
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            std::cout << A_at(M, rows, i, j) << "\t";
        }
        std::cout << "\n";
    }
}

// ================= 1. Итерационный однопараметрический метод =================

int param_method(const std::vector<double> &A, const std::vector<double> &b,
                 std::vector<double> &x, int n,
                 double tau, double tol = 1e-10, int maxiter = 200000) {
    std::vector<double> r(n), Ax(n), x_prev(n);

    for (int k = 0; k < maxiter; ++k) {
        cblas_dgemv(
                CblasColMajor, CblasNoTrans,
                n, n,
                1.0,
                A.data(), n,
                x.data(), 1,
                0.0,
                Ax.data(), 1
        ); // Для вычисления Ax

        // r = b - Ax
        for (int i = 0; i < n; ++i) {
            r[i] = b[i] - Ax[i];
        }

        x_prev = x;

        // x = x + tau * r
        cblas_daxpy(n, tau, r.data(), 1, x.data(), 1);

        // r := x - x_prev
        for (int i = 0; i < n; ++i) {
            r[i] = x[i] - x_prev[i];
        }

        // ||x - x_prev||_2
        double norm_diff = cblas_dnrm2(n, r.data(), 1);

        if (norm_diff < tol) {
            return k + 1;
        }
    }

    return maxiter;
}


// ================= 2. Решение через разложение Холецкого =================

std::vector<double> cholesky_solve(std::vector<double> A, std::vector<double> b, int n) {
    LAPACKE_dpotrf(LAPACK_COL_MAJOR, 'L', n, A.data(), n); // Double Precision Orthogonal TRiangular Factorization

    LAPACKE_dpotrs(LAPACK_COL_MAJOR, 'L', n, 1, A.data(), n, b.data(), n);

    return b;
}

// ================= 3. SVD (dgesvd) =================

void svd_decomposition(const std::vector<double> &A_src, int m, int n) {
    std::vector<double> A = A_src;

    int minmn = std::min(m, n);
    std::vector<double> S(minmn);
    std::vector<double> U(m * m);
    std::vector<double> VT(n * n);
    std::vector<double> superb(minmn - 1);

    LAPACKE_dgesvd(
            LAPACK_COL_MAJOR,
            'A', 'A',         // полный U и V^T
            m, n,
            A.data(), m,
            S.data(),
            U.data(), m,
            VT.data(), n,
            superb.data()
    ); // double GEneral SV Decomposition

    std::cout << "=== SVD DECOMPOSITION ===\n";
    std::cout << "U matrix:\n";
    print_matrix(U, m, m);
    std::cout << "\nSigma diagonal:\n";
    print_vector(S);
    std::cout << "\nV^T matrix:\n";
    print_matrix(VT, n, n);
    std::cout << "\n";
}

// ================= 4. LU-Разложение (dgetrf) =================

void lu_decomposition(const std::vector<double> &A_src, int n) {
    std::vector<double> A = A_src;
    std::vector<lapack_int> ipiv(n);

    LAPACKE_dgetrf(LAPACK_COL_MAJOR, n, n, A.data(), n, ipiv.data());

    // В A лежит смешанная матрица LU.
    std::vector<double> L(n * n, 0.0);
    std::vector<double> U(n * n, 0.0);

    for (int i = 0; i < n; ++i) {
        A_at(L, n, i, i) = 1.0;

        for (int j = 0; j < n; ++j) {
            if (i > j) {
                A_at(L, n, i, j) = A_at(A, n, i, j);
            } else {
                A_at(U, n, i, j) = A_at(A, n, i, j);
            }
        }
    }

    std::cout << "=== LU DECOMPOSITION ===\n";
    std::cout << "L matrix:\n";
    print_matrix(L, n, n);
    std::cout << "\nU matrix:\n";
    print_matrix(U, n, n);
    std::cout << "\nPivot indices: ";
    for (int i = 0; i < n; ++i) {
        std::cout << (ipiv[i] - 1) << " ";
    }
    std::cout << "\n\n";
}

// ================= 5. Собственные значения/векторы (dsyev) =================

void eigen_decomposition(const std::vector<double> &A_src, int n) {
    std::vector<double> A = A_src;
    std::vector<double> w(n);

    LAPACKE_dsyev(
            LAPACK_COL_MAJOR,
            'V', 'U',         // собственные значения и векторы, верхний треугольник
            n,
            A.data(), n,
            w.data()
    );

    std::cout << "=== EIGEN DECOMPOSITION ===\n";
    std::cout << "Eigenvalues real: ";
    print_vector(w);
    std::cout << "Eigenvalues imag: ";
    for (int i = 0; i < n; ++i) std::cout << "0 ";
    std::cout << "\nEigenvectors:\n";
    print_matrix(A, n, n);
    std::cout << "\n";
}

int main() {
    system("chcp 65001");
    std::cout.setf(std::ios::fixed);
    std::cout.precision(6);

    int n = 3;
    std::vector<double> A = {
            4.0, 1.0, 1.0,
            1.0, 3.0, 0.0,
            1.0, 0.0, 2.0
    };

    std::vector<double> b = {1.0, 2.0, 3.0};

    // Для итерационного метода найдём λ_min и λ_max (через dsyev)
    std::vector<double> A_eig = A;
    std::vector<double> w(n);
    LAPACKE_dsyev(LAPACK_COL_MAJOR, 'N', 'U', n, A_eig.data(), n, w.data());
    double lambda_min = w[0];
    double lambda_max = w[n - 1];
    double tau_opt = 2.0 / (lambda_min + lambda_max);

    // ---------- Решение СЛАУ ----------
    std::vector<double> x_iter(n, 0.0);
    int iters = param_method(A, b, x_iter, n, tau_opt);

    std::vector<double> x_chol = cholesky_solve(A, b, n);

    std::cout << "=== SOLUTIONS ===\n";
    std::cout << "Iterative method (" << iters << " iterations): ";
    print_vector(x_iter);
    std::cout << "Cholesky method: ";
    print_vector(x_chol);
    std::cout << "\n";

    // ---------- SVD ----------
    svd_decomposition(A, n, n);

    // ---------- LU ----------
    lu_decomposition(A, n);

    // ---------- Eigen ----------
    eigen_decomposition(A, n);

    return 0;
}
