from typing import Callable, Tuple
import argparse
import sys

PRINT_MAX_LINE_LENGTH = 80
DEBUG = False


def score_fun(a: str,
              b: str,
              match_score: int = 5,
              mismatch_score: int = -4) -> int:
    return match_score if a == b else mismatch_score


def needleman_wunsch(seq1: str,
                     seq2: str,
                     score_fun: Callable[[str, str], int] = score_fun,
                     gap_penalty: int = -10) -> Tuple[int, str, str]:
    """Given two sequences, aligns them using the Needleman-Wunsch algorithm.

    This function takes two sequences and optionally a scoring function and a
    gap penalty value as arguments. 
    The function returns a tuple containing the optimal alignment score and the
    aligned sequences, e.g. (10, 'ACCGT', 'AC-GT').

    Args:
        seq1: The first sequence, e.g. 'ACCGT'
        seq2: The second sequence, e.g. 'ACGT'
        score_fun: The scoring function, e.g. score_fun('A', 'A') returns 5
        gap_penalty: The gap penalty value, e.g. -10

    Returns:
        score: The optimal alignment score, e.g. 10
        aligned_seq1: The first aligned sequence, e.g. 'ACCGT'
        aligned_seq2: The second aligned sequence, e.g. 'AC-GT'
    """
    n, m = len(seq1), len(seq2)

    # Матрицы очков и указателей
    D = [[0] * (m + 1) for _ in range(n + 1)]
    Ptr = [[None] * (m + 1) for _ in range(n + 1)]

    # Инициализация границ
    for i in range(1, n + 1):
        D[i][0] = i * gap_penalty
        Ptr[i][0] = 'U'
    for j in range(1, m + 1):
        D[0][j] = j * gap_penalty
        Ptr[0][j] = 'L'

    # Заполнение DP
    for i in range(1, n + 1):
        ai = seq1[i - 1]
        for j in range(1, m + 1):
            bj = seq2[j - 1]
            diag = D[i - 1][j - 1] + score_fun(ai, bj)  # S(i,j)
            left = D[i][j - 1] + gap_penalty  # LEFT
            up = D[i - 1][j] + gap_penalty  # UP

            # DIAG > LEFT > UP
            best, ptr = diag, 'D'
            if left > best:
                best, ptr = left, 'L'
            if up > best:
                best, ptr = up, 'U'

            D[i][j] = best
            Ptr[i][j] = ptr

    # Бэктрейс
    i, j = n, m
    a_rev, b_rev = [], []
    while i > 0 or j > 0:
        p = Ptr[i][j] if i >= 0 and j >= 0 else None
        if i > 0 and j > 0 and p == 'D':
            a_rev.append(seq1[i - 1])
            b_rev.append(seq2[j - 1])
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or p == 'L'):
            a_rev.append('-')
            b_rev.append(seq2[j - 1])
            j -= 1
        else:  # 'U' или j == 0
            a_rev.append(seq1[i - 1])
            b_rev.append('-')
            i -= 1

    aligned_seq1 = ''.join(reversed(a_rev))
    aligned_seq2 = ''.join(reversed(b_rev))
    return D[n][m], aligned_seq1, aligned_seq2


def print_array(matrix: list):
    for row in matrix:
        for element in row:
            print(f"{element:6}", end="")
        print()


def print_results(seq1: str, seq2: str, score: int, file=None):
    """Prints the results of the Needleman-Wunsch algorithm.

    This function takes two aligned sequences and the optimal alignment score
    as arguments. It prints the sequences and the score to the standard output
    or to a file.

    Args:
        seq1: The first aligned sequence, e.g. 'ACCGT'
        seq2: The second aligned sequence, e.g. 'AC-GT'
        score: The optimal alignment score, e.g. 10
        file: The file to print to. If None, prints to the standard output.

    Returns:
        None
    """
    if file is None:
        file = sys.stdout

    def print_subseq(i, n, s):
        print("%s: %s" % (n, s[i: i + PRINT_MAX_LINE_LENGTH]), file=file)

    print("Pairwise alignment:", file=file)
    for i in range(0, len(seq1), PRINT_MAX_LINE_LENGTH):
        print_subseq(i, 'seq1', seq1)
        print_subseq(i, 'seq2', seq2)
        print(file=file)
    print("Score: %s" % score, file=file)


def main():
    parser = argparse.ArgumentParser(description='Needleman-Wunsch algorithm')
    parser.add_argument('seq1', help='first sequence')
    parser.add_argument('seq2', help='second sequence')
    parser.add_argument('--match', type=int, help='match score')
    parser.add_argument('--mismatch', type=int, help='mismatch score')
    parser.add_argument('--gap', type=int, default=-10, help='gap penalty')
    parser.add_argument('--debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug
    print(args.match, args.mismatch, args.gap)

    if args.match and args.mismatch:
        score, aln1, aln2 = needleman_wunsch(args.seq1,
                                             args.seq2,
                                             score_fun=lambda x, y: args.match if x == y else args.mismatch,
                                             gap_penalty=args.gap)
    else:
        assert not args.match and not args.mismatch, "match and mismatch must be specified together"
        score, aln1, aln2 = needleman_wunsch(args.seq1,
                                             args.seq2,
                                             score_fun=score_fun,
                                             gap_penalty=args.gap)
    print_results(aln1, aln2, score)

    return score, aln1, aln2


if __name__ == '__main__':
    main()
