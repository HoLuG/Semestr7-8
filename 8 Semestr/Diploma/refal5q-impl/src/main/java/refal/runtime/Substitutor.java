package refal.runtime;

import refal.ast.Br;
import refal.ast.Call;
import refal.ast.Term;
import refal.ast.Var;
import refal.deque.Expr;

// Подстановка связываний в правую часть правила.
// e-переменная разворачивается через Expr.concat — O(1) аморт.
public final class Substitutor {

    private Substitutor() {
    }

    public static Expr<Term> substitute(Iterable<Term> result, Bindings env) {
        Expr<Term> out = Expr.empty();
        for (Term t : result) {
            switch (t) {
                case Var v -> {
                    String key = v.key();
                    if (!env.contains(key)) {
                        throw new IllegalStateException(
                                "Unbound variable in result: " + key);
                    }
                    // концатенация — O(1) аморт.
                    out = Expr.concat(out, env.get(key));
                }
                case Br br -> {
                    Expr<Term> inner = substitute(br.items(), env);
                    out = out.pushBack(new Br(inner));
                }
                case Call c -> {
                    Expr<Term> argDq = substitute(c.args(), env);
                    out = out.pushBack(new Call(c.fn(), argDq));
                }
                default -> out = out.pushBack(t);
            }
        }
        return out;
    }
}
