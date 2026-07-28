import src.nw as align


def test_nw_1():
    """Identical sequences, match=5, mismatch=-4, gap=-10
    """
    seq1 = 'ACGT'
    seq2 = 'ACGT'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 5 if x == y else -4,
                                                               gap_penalty=-10)
    assert score == 20
    assert aligned_seq1 == 'ACGT'
    assert aligned_seq2 == 'ACGT'
    print("test_nw_1 passed")


def test_nw_2():
    """Both sequences empty, match=2, mismatch=-1, gap=-3
    """
    seq1 = ''
    seq2 = ''
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 2 if x == y else -1,
                                                               gap_penalty=-3)
    assert score == 0
    assert aligned_seq1 == ''
    assert aligned_seq2 == ''
    print("test_nw_2 passed")


def test_nw_3():
    """One sequence empty, match=2, mismatch=-1, gap=-2
    """
    seq1 = 'ACGT'
    seq2 = ''
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 2 if x == y else -1,
                                                               gap_penalty=-2)
    assert score == -8
    assert aligned_seq1 == 'ACGT'
    assert aligned_seq2 == '----'
    print("test_nw_3 passed")


def test_nw_4():
    """All mismatches, match=1, mismatch=-5, gap=-1
    """
    seq1 = 'AAAA'
    seq2 = 'TTTT'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 1 if x == y else -5,
                                                               gap_penalty=-1)
    assert score == -8
    assert aligned_seq1 == 'AAAA----'
    assert aligned_seq2 == '----TTTT'
    print("test_nw_4 passed")


def test_nw_5():
    """All mismatches, match=1, mismatch=-1, gap=-10
    """
    seq1 = 'AAAA'
    seq2 = 'TTTT'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 1 if x == y else -1,
                                                               gap_penalty=-10)
    assert score == -4
    assert aligned_seq1 == 'AAAA'
    assert aligned_seq2 == 'TTTT'
    print("test_nw_5 passed")


def test_nw_6():
    """Different lengths, match=2, mismatch=-1, gap=-5
    """
    seq1 = 'ACGTG'
    seq2 = 'ACGT'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 2 if x == y else -1,
                                                               gap_penalty=-5)
    assert score == 3
    assert aligned_seq1 == 'ACGTG'
    assert aligned_seq2 == 'ACGT-'
    print("test_nw_6 passed")


def test_nw_7():
    """Tie-break case, match=1, mismatch=-1, gap=0
    """
    seq1 = 'A'
    seq2 = 'A'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 1 if x == y else -1,
                                                               gap_penalty=0)
    assert aligned_seq1 == 'A'
    assert aligned_seq2 == 'A'
    assert score == 1
    print("test_nw_7 passed")


def test_nw_8():
    """Trailing gaps, match=2, mismatch=-1, gap=-2
    """
    seq1 = 'AC'
    seq2 = 'ACGT'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 2 if x == y else -1,
                                                               gap_penalty=-2)
    assert score == 0
    assert aligned_seq1 == 'AC--'
    assert aligned_seq2 == 'ACGT'
    print("test_nw_8 passed")


def test_nw_9():
    """Reversed sequences, match=5, mismatch=-4, gap=-1
    """
    seq1 = 'ABCDEF'
    seq2 = 'FEDCBA'
    score, aligned_seq1, aligned_seq2 = align.needleman_wunsch(seq1,
                                                               seq2,
                                                               score_fun=lambda x, y: 5 if x == y else -4,
                                                               gap_penalty=-1)
    assert score == -5
    assert aligned_seq1 == 'ABCDEF-----'
    assert aligned_seq2 == '-----FEDCBA'
    print("test_nw_9 passed")


if __name__ == "__main__":
    for f in [test_nw_1, test_nw_2, test_nw_3, test_nw_4,
              test_nw_5, test_nw_6, test_nw_7, test_nw_8, test_nw_9]:
        f()
    print("All tests passed!")
