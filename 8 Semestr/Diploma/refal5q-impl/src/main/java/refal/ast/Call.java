package refal.ast;

import refal.deque.Expr;

import java.util.Objects;

// Вызов функции <Name args>. Допустим только в правой части правила.
public record Call(String fn, Expr<Term> args) implements Term {
    public Call {
        Objects.requireNonNull(fn, "Call.fn");
        if (fn.isEmpty()) {
            throw new IllegalArgumentException("Call.fn must not be empty");
        }
        Objects.requireNonNull(args, "Call.args");
    }
}
