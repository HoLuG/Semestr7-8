from __future__ import annotations
from typing import Protocol, Optional
import math


# =============================
#  Абстракция MatrixStorage
# =============================
# Интерфейс, определяющий поведение любой матрицы,
# используемой в алгоритме Needleman–Wunsch
# Методы:
#   get(i, j) — получить значение ячейки [i][j]
#   set(i, j, value) — записать значение
#   is_valid(i,j) — проверить, находится ли ячейка в допустимой зоне (например, в пределах полосы)
#   shape() — вернуть размер матрицы (число строк и столбцов)
class MatrixStorage(Protocol):
    def get(self, i: int, j: int) -> float: ...
    def set(self, i: int, j: int, value: float) -> None: ...
    def is_valid(self, i: int, j: int) -> bool: ...
    def shape(self) -> tuple[int, int]: ...


# =============================
#  Реализация полной матрицы (FullMatrix)
# =============================
# Класс, реализующий хранение всей матрицы выравнивания (n+1) * (m+1)
# Используется для проверки корректности полосного алгоритма (без ограничения k)
# Методы:
#   __init__(n, m=None, k=0) — создаёт полную матрицу заданного размера (n+1)x(m+1)
#   shape() -> (n, m) — возвращает размеры матрицы
#   is_valid(i, j) -> bool — проверяет, допустимы ли индексы (в пределах диапазона и полосы k)
#   get(i, j) -> float — возвращает значение ячейки (или -inf, если она вне диапазона)
#   set(i, j, value) -> None — записывает значение в ячейку, если она допустима
class FullMatrix:
    def __init__(self, n: int, m: Optional[int] = None, k: int = 0) -> None:
        self.n = n
        self.m = n if m is None else m
        self.k = k
        self.mat = [[-math.inf] * (self.m + 1) for _ in range(self.n + 1)]

    def shape(self) -> tuple[int, int]:
        return self.n, self.m

    def is_valid(self, i: int, j: int) -> bool:
        return 0 <= i <= self.n and 0 <= j <= self.m and abs(i - j) <= self.k

    def get(self, i: int, j: int) -> float:
        if self.is_valid(i, j):
            return self.mat[i][j]
        return -math.inf

    def set(self, i: int, j: int, value: float) -> None:
        if self.is_valid(i, j):
            self.mat[i][j] = value


# =============================
#  Реализация полосной матрицы (BandedMatrix)
# =============================
# Класс, реализующий оптимизированное хранение матрицы выравнивания —
# только в пределах диагональной полосы шириной 2k+1
# Методы:
#   __init__(n, m=None, k=0) — создаёт полосную матрицу нужной ширины (2k+1) и размера n+1
#   shape() -> (n, m) — возвращает размеры матрицы
#   index(i, j) -> Optional[int] — переводит координаты (i,j) в индекс столбца внутри полосы (если допустимо)
#   is_valid(i, j) -> bool — проверяет, находится ли ячейка в пределах полосы и границ матрицы
#   get(i, j) -> float — возвращает значение ячейки (или -inf, если она вне допустимой области)
#   set(i, j, value) -> None — записывает значение в ячейку, если она допустима
class BandedMatrix:
    def __init__(self, n: int, m: Optional[int] = None, k: int = 0) -> None:
        self.n = n
        self.m = n if m is None else m
        self.k = k
        self.width = 2 * k + 1
        self._rows = [[-math.inf] * self.width for _ in range(self.n + 1)]

    def shape(self) -> tuple[int, int]:
        return self.n, self.m

    def index(self, i: int, j: int) -> Optional[int]:
        b = j - (i - self.k)
        if 0 <= b < self.width:
            return b
        return None

    def is_valid(self, i: int, j: int) -> bool:
        return 0 <= i <= self.n and 0 <= j <= self.m and abs(i - j) <= self.k

    def get(self, i: int, j: int) -> float:
        if not self.is_valid(i, j):
            return -math.inf
        b = self.index(i, j)
        if b is None:
            return -math.inf
        return self._rows[i][b]

    def set(self, i: int, j: int, value: float) -> None:
        if not self.is_valid(i, j):
            return
        b = self.index(i, j)
        if b is None:
            return
        self._rows[i][b] = value


# ======================================
#  Алгоритм Needleman–Wunsch с ограничением полосы
# ======================================
# Функция вычисляет максимальную оценку глобального выравнивания двух строк seq1 и seq2
# Аргументы:
#   seq1, seq2 — сравниваемые последовательности
#   matrix — объект, реализующий интерфейс MatrixStorage
#   match, mismatch, gap — оценки (награды и штрафы) за совпадение, несовпадение и пропуск
# Возвращает:
#   float — финальная оценка (score) выравнивания
def needleman_wunsch(
    seq1: str,
    seq2: str,
    matrix: MatrixStorage,
    match: int = 5,
    mismatch: int = -4,
    gap: int = -10,
) -> float:
    n, m = len(seq1), len(seq2)
    N, M = matrix.shape()
    assert (n, m) == (N, M)

    # Функция подсчёта совпадений/несовпадений между символами
    def s(a: str, b: str) -> int:
        return match if a == b else mismatch

    # Инициализация первой ячейки
    if matrix.is_valid(0, 0):
        matrix.set(0, 0, 0.0)

    # Заполнение первой колонки (вставки относительно seq2)
    for i in range(1, n + 1):
        if not matrix.is_valid(i, 0):
            continue
        prev = matrix.get(i - 1, 0)
        matrix.set(i, 0, prev + gap if prev != -math.inf else -math.inf)

    # Заполнение первой строки (вставки относительно seq1)
    for j in range(1, m + 1):
        if not matrix.is_valid(0, j):
            continue
        prev = matrix.get(0, j - 1)
        matrix.set(0, j, prev + gap if prev != -math.inf else -math.inf)

    # Основной двойной цикл: заполнение матрицы выравнивания
    for i in range(1, n + 1):
        # ограничиваем j только допустимой полосой
        j_min = max(1, i - matrix.k, 0)
        j_max = min(m, i + matrix.k)
        for j in range(j_min, j_max + 1):
            if not matrix.is_valid(i, j):
                continue
            diag = matrix.get(i - 1, j - 1)  # переход по диагонали
            up = matrix.get(i - 1, j)        # сверху (gap в seq2)
            left = matrix.get(i, j - 1)      # слева (gap в seq1)

            best = -math.inf
            if diag != -math.inf:
                best = max(best, diag + s(seq1[i - 1], seq2[j - 1]))
            if up != -math.inf:
                best = max(best, up + gap)
            if left != -math.inf:
                best = max(best, left + gap)

            # сохраняем лучший вариант в ячейку
            matrix.set(i, j, best)

    return matrix.get(n, m)


# Запускает алгоритм дважды — с полосой k и (k+1),
# чтобы проверить монотонность: расширение полосы не должно ухудшать результат.
# Возвращает кортеж из двух оценок (score_k, score_k+1)
def run_with_both(seq1: str, seq2: str, k: int, match=5, mismatch=-4, gap=-10) -> tuple[float, float]:
    n, m = len(seq1), len(seq2)
    score_k = needleman_wunsch(seq1, seq2, BandedMatrix(n, m, k), match, mismatch, gap)
    score_k1 = needleman_wunsch(seq1, seq2, BandedMatrix(n, m, k + 1), match, mismatch, gap)
    return score_k, score_k1


# Вычисляет классический результат Needleman–Wunsch (без ограничений полосы)
def classic_full_score(seq1: str, seq2: str, match=5, mismatch=-4, gap=-10) -> float:
    n, m = len(seq1), len(seq2)
    mat = FullMatrix(n, m, k=max(n, m))
    return needleman_wunsch(seq1, seq2, mat, match, mismatch, gap)
