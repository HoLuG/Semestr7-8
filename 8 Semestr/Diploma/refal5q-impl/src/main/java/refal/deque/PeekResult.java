package refal.deque;

import java.util.Objects;

// Результат separateFront/separateBack: отделённый терм и остаток выражения.
public record PeekResult<T>(T term, Expr<T> rest) {
    public PeekResult {
        Objects.requireNonNull(term, "PeekResult.term");
        Objects.requireNonNull(rest, "PeekResult.rest");
    }
}
