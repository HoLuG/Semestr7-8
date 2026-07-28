import src.main as align


# Идентичные строки
def test_identical_sequences_equal_length():
    seq = "ACGT"
    n = len(seq)
    k = 0
    s_band = align.needleman_wunsch(seq, seq, align.BandedMatrix(n, n, k), match=5, mismatch=-4, gap=-10)
    s_full_band = align.needleman_wunsch(seq, seq, align.FullMatrix(n, n, k), match=5, mismatch=-4, gap=-10)
    assert s_band == 4 * 5
    assert s_band == s_full_band


# Пустые строки: корректная инициализация границ и нулевой скор
def test_empty_sequences():
    s_band = align.needleman_wunsch("", "", align.BandedMatrix(0, 0, k=0), match=2, mismatch=-1, gap=-3)
    s_full_band = align.needleman_wunsch("", "", align.FullMatrix(0, 0, k=0), match=2, mismatch=-1, gap=-3)
    assert s_band == 0
    assert s_band == s_full_band


# Одна строка пустая: проверка заполнения первой колонки (сплошные gap’ы)
def test_one_empty():
    seq1 = "ACGT"
    seq2 = ""
    k = len(seq1)
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(len(seq1), 0, k=k), match=2, mismatch=-1, gap=-2)
    s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(len(seq1), 0, k=k), match=2, mismatch=-1, gap=-2)
    assert s_band == len(seq1) * -2
    assert s_band == s_full_band


# Все несовпадения и «мягкий» штраф за разрыв: выгоднее вставить большие разрывы
def test_all_mismatches_prefers_gaps_when_gap_is_small():
    seq1, seq2 = "AAAA", "TTTT"
    k = len(seq1)
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(4, 4, k), match=1, mismatch=-5, gap=-1)
    s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(4, 4, k), match=1, mismatch=-5, gap=-1)
    assert s_band == -8
    assert s_band == s_full_band


# Все несовпадения и «жёсткий» штраф за разрыв: выгоднее выровнять без разрывов
def test_all_mismatches_align_direct_when_gap_is_harsh():
    seq1, seq2 = "AAAA", "TTTT"
    k = len(seq1)
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(4, 4, k), match=1, mismatch=-1, gap=-10)
    s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(4, 4, k), match=1, mismatch=-1, gap=-10)
    assert s_band == -4
    assert s_band == s_full_band


# Разная длина (задача со звёздочкой m != n)
def test_different_lengths():
    seq1, seq2 = "ACGTG", "ACGT"
    k = max(len(seq1), len(seq2))
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(len(seq1), len(seq2), k), match=2, mismatch=-1, gap=-5)
    s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(len(seq1), len(seq2), k), match=2, mismatch=-1, gap=-5)
    assert s_band == 3
    assert s_band == s_full_band

    s_full = align.classic_full_score(seq1, seq2, match=2, mismatch=-1, gap=-5)
    assert s_band == s_full


# Тривиальный tie-break (k=0): проверяем, что совпадения дают 1
def test_tie_break_no_band_issue():
    s_band = align.needleman_wunsch("A", "A", align.BandedMatrix(1, 1, k=0), match=1, mismatch=-1, gap=0)
    s_full_band = align.needleman_wunsch("A", "A", align.FullMatrix(1, 1, k=0), match=1, mismatch=-1, gap=0)
    assert s_band == 1
    assert s_band == s_full_band


# Хвостовые разрывы: проверка корректного добора разрывов в конце
def test_trailing_gaps():
    seq1, seq2 = "AC", "ACGT"
    k = len(seq2)
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(len(seq1), len(seq2), k), match=2, mismatch=-1, gap=-2)
    s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(len(seq1), len(seq2), k), match=2, mismatch=-1, gap=-2)
    assert s_band == 0
    assert s_band == s_full_band


# Использует функцию run_with_both для проверки конкретного k, при котором увеличение не меняет score
def test_k_vs_k_plus():
    # Случай 1: Идентичные последовательности - k=0 достаточно
    seq1, seq2 = "ACGT", "ACGT"
    s_k0, s_k1 = align.run_with_both(seq1, seq2, k=0, match=5, mismatch=-4, gap=-10)
    s_full = align.classic_full_score(seq1, seq2, match=5, mismatch=-4, gap=-10)
    # При k=0 уже достигнут оптимум, увеличение до k=1 не меняет результат
    assert s_k0 == s_k1 == s_full == 4 * 5
    
    # Случай 2: Последовательности одинаковой длины, где требуется k=1 для оптимального результата
    seq3, seq4 = "ACGTACGT", "TGCATGCA"  # перевернутые последовательности требуют k=1
    s_k0 = align.needleman_wunsch(seq3, seq4, align.BandedMatrix(8, 8, k=0), match=5, mismatch=-4, gap=-10)
    s_k1, s_k2 = align.run_with_both(seq3, seq4, k=1, match=5, mismatch=-4, gap=-10)
    s_full2 = align.classic_full_score(seq3, seq4, match=5, mismatch=-4, gap=-10)
    assert s_k0 != s_full2
    assert s_k1 == s_k2 == s_full2 == -21.0  # при k=1 уже оптимальный
    
    # Случай 3: Последовательности, где требуется k=2 для оптимального результата
    seq5, seq6 = "ACGTACGT", "ACGTACGTAC"  # вставка в конце требует k=2
    # Проверяем, что при k=1 путь недостижим (-inf), а при k=2 уже достигнут оптимум
    s_k1_case3 = align.needleman_wunsch(seq5, seq6, align.BandedMatrix(len(seq5), len(seq6), k=1), match=5, mismatch=-4, gap=-10)
    s_k2_case3, s_k3_case3 = align.run_with_both(seq5, seq6, k=2, match=5, mismatch=-4, gap=-10)
    s_full3 = align.classic_full_score(seq5, seq6, match=5, mismatch=-4, gap=-10)
    # При k=1 путь недостижим (из-за вставки в конце)
    assert align.math.isinf(s_k1_case3)
    # При k=2 уже достигнут оптимум, увеличение до k=3 не меняет результат
    assert s_k2_case3 == s_k3_case3 == s_full3 == 20.0
    assert s_k1_case3 != s_k2_case3
    
    # Случай 4: Последовательности одинаковой длины, где требуется k=2 для оптимального результата
    seq7, seq8 = "ACGTACGT", "GTACGTAC"  # циклический сдвиг требует k=2
    s_k0_case4 = align.needleman_wunsch(seq7, seq8, align.BandedMatrix(8, 8, k=0), match=5, mismatch=-4, gap=-10)
    s_k1_case4 = align.needleman_wunsch(seq7, seq8, align.BandedMatrix(8, 8, k=1), match=5, mismatch=-4, gap=-10)
    s_k2_case4, s_k3_case4 = align.run_with_both(seq7, seq8, k=2, match=5, mismatch=-4, gap=-10)
    s_full4 = align.classic_full_score(seq7, seq8, match=5, mismatch=-4, gap=-10)
    assert s_k0_case4 < s_full4
    assert s_k1_case4 < s_full4
    assert s_k2_case4 == s_k3_case4 == s_full4 == -10.0

# Сравнение Banded vs Full при разных k
def test_banded_equals_full_when_band_is_wide():
    seq1, seq2 = "ACGTACGT", "ACGTACCT"
    n, m = len(seq1), len(seq2)
    for k in [0, 1, 2, 3, max(n, m)]:
        s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(n, m, k), match=1, mismatch=-1, gap=-1)
        s_full_band = align.needleman_wunsch(seq1, seq2, align.FullMatrix(n, m, k), match=1, mismatch=-1, gap=-1)
        assert s_band == s_full_band

    # Итоговая проверка на «полную» матрицу при широкой полосе
    k = max(n, m)
    s_band = align.needleman_wunsch(seq1, seq2, align.BandedMatrix(n, m, k), match=1, mismatch=-1, gap=-1)
    s_full = align.classic_full_score(seq1, seq2, match=1, mismatch=-1, gap=-1)
    assert s_band == s_full
