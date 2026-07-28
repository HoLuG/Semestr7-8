package refal.ast;

import refal.deque.Expr;

import java.util.Objects;

// Скобочный терм: хранит вложенное выражение как Expr<Term>.
public record Br(Expr<Term> items) implements Term {
    public Br {
        Objects.requireNonNull(items, "Br.items");
    }
}
