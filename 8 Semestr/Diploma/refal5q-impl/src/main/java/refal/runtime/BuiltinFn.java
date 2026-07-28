package refal.runtime;

import refal.ast.Term;
import refal.deque.Expr;

// Сигнатура встроенной функции: аргументы и результат — деки термов.
@FunctionalInterface
public interface BuiltinFn {
    Expr<Term> apply(Runtime rt, Expr<Term> args);
}
