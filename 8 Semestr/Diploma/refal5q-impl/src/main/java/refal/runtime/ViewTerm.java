package refal.runtime;

import refal.ast.Term;
import refal.deque.Expr;

// Элементарная единица поля зрения: Call и Br разворачиваются в линейную
// последовательность маркеров-открывашек/закрывашек + пассивные термы.
public sealed interface ViewTerm
        permits ViewTerm.Passive,
                ViewTerm.BulkPassive,
                ViewTerm.AngOpen,
                ViewTerm.AngClose,
                ViewTerm.ParenOpen,
                ViewTerm.ParenClose {

    record Passive(Term term) implements ViewTerm {
    }

    /**
     * Последовательность пассивных термов, хранящаяся как единица Expr;Term;.
     * Семантически эквивалентна Passive(items[0]), ..., Passive(items[n-1]),
     * но позволяет передавать e-переменные на стек в O(1) вместо O(n).
     */
    record BulkPassive(Expr<Term> items) implements ViewTerm {
    }

    record AngOpen(String fn) implements ViewTerm {
    }

    record AngClose() implements ViewTerm {
        public static final AngClose INSTANCE = new AngClose();
    }

    record ParenOpen() implements ViewTerm {
        public static final ParenOpen INSTANCE = new ParenOpen();
    }

    record ParenClose() implements ViewTerm {
        public static final ParenClose INSTANCE = new ParenClose();
    }
}
