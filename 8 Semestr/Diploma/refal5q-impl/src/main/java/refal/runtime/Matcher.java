package refal.runtime;

import refal.ast.Br;
import refal.ast.EVar;
import refal.ast.SVar;
import refal.ast.TVar;
import refal.ast.Term;
import refal.ast.Var;
import refal.deque.Expr;
import refal.deque.PeekResult;

import java.util.Iterator;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.function.Supplier;


public final class Matcher {

    private Matcher() {
    }

    private sealed interface Thunk permits Thunk.Done, Thunk.More {
        record Done(Optional<Bindings> value) implements Thunk {}
        record More(Supplier<Thunk> next) implements Thunk {}

        static Optional<Bindings> run(Thunk start) {
            Thunk t = start;
            while (t instanceof More m) {
                t = m.next().get();
            }
            return ((Done) t).value();
        }
    }

    // ---- Публичный API --------------------------------------------------

    public static Optional<Bindings> match(List<Term> pattern, List<Term> expr) {
        return match(pattern, Expr.fromList(expr));
    }

    public static Optional<Bindings> match(List<Term> pattern, Expr<Term> expr) {
        return Thunk.run(rec(pattern, 0, pattern.size(), expr, Bindings.empty(),
                env -> new Thunk.Done(Optional.of(env))));
    }

    // ---- Ядро -----------------------------------------------------------

    private static Thunk rec(
            List<Term> pat, int pi, int pe,
            Expr<Term> expr, Bindings env,
            Function<Bindings, Thunk> cont) {

        // Двусторонняя «прогонка»: пока хотя бы один конец — не e-переменная.
        while (pi < pe) {
            Term left = pat.get(pi);
            Term right = pat.get(pe - 1);

            boolean leftEvar = left instanceof EVar;
            boolean rightEvar = right instanceof EVar;

            if (leftEvar && rightEvar) {
                break;
            }

            if (!leftEvar) {
                if (expr.isEmpty()) {
                    return new Thunk.Done(Optional.empty());
                }
                PeekResult<Term> pr = expr.separateFront();
                Term consumed = pr.term();
                Expr<Term> rest = pr.rest();
                final int newPi = pi + 1;
                final int finalPe = pe;
                final Expr<Term> finalRest = rest;
                final Function<Bindings, Thunk> outerCont = cont;
                return matchSingleAll(left, consumed, env,
                        env1 -> new Thunk.More(
                                () -> rec(pat, newPi, finalPe, finalRest, env1, outerCont)));
            }
            // leftEvar, !rightEvar
            if (expr.isEmpty()) {
                return new Thunk.Done(Optional.empty());
            }
            PeekResult<Term> pr = expr.separateBack();
            Term consumed = pr.term();
            Expr<Term> rest = pr.rest();
            final int finalPi = pi;
            final int newPe = pe - 1;
            final Expr<Term> finalRest = rest;
            final Function<Bindings, Thunk> outerCont = cont;
            return matchSingleAll(right, consumed, env,
                    env1 -> new Thunk.More(
                            () -> rec(pat, finalPi, newPe, finalRest, env1, outerCont)));
        }

        // Образец исчерпан.
        if (pi == pe) {
            return expr.isEmpty()
                    ? cont.apply(env)
                    : new Thunk.Done(Optional.empty());
        }

        EVar leftV = (EVar) pat.get(pi);
        String key = leftV.key();

        // Ровно одна e-переменная в остатке.
        if (pi == pe - 1) {
            if (env.contains(key)) {
                if (!Bindings.equalExprs(env.get(key), expr)) {
                    return new Thunk.Done(Optional.empty());
                }
                return cont.apply(env);
            }
            return cont.apply(env.with(key, expr));
        }

        // Несколько e-переменных: повторное вхождение — длина зафиксирована.
        if (env.contains(key)) {
            Expr<Term> bound = env.get(key);
            int len = bound.size();
            if (expr.size() < len) {
                return new Thunk.Done(Optional.empty());
            }
            Expr<Term> consumed = takeFront(expr, len);
            if (!Bindings.equalExprs(consumed, bound)) {
                return new Thunk.Done(Optional.empty());
            }
            Expr<Term> rest = dropFront(expr, len);
            return new Thunk.More(() -> rec(pat, pi + 1, pe, rest, env, cont));
        }

        // Свежая e-переменная: перебор длин 0..size.
        return tryEVar(pat, pi, pe, key, Expr.empty(), expr, env, cont);
    }

    // Перебирает длины для свежей e-переменной итеративно через Thunk,
    // не рекурсивно — глубина стека O(1).
    private static Thunk tryEVar(
            List<Term> pat, int pi, int pe,
            String key,
            Expr<Term> consumed, Expr<Term> remaining,
            Bindings env,
            Function<Bindings, Thunk> cont) {

        Bindings env1 = env.with(key, consumed);
        Function<Bindings, Thunk> outerCont = cont;
        Thunk attempt = new Thunk.More(
                () -> rec(pat, pi + 1, pe, remaining, env1, outerCont));
        // Вычисляем немедленно, чтобы можно было перейти к следующей длине
        // если attempt вернул empty. «Немедленно» — значит через run одного шага.
        Optional<Bindings> r = Thunk.run(attempt);
        if (r.isPresent()) {
            return new Thunk.Done(r);
        }
        if (remaining.isEmpty()) {
            return new Thunk.Done(Optional.empty());
        }
        PeekResult<Term> pr = remaining.separateFront();
        Expr<Term> newConsumed = consumed.pushBack(pr.term());
        Expr<Term> newRemaining = pr.rest();
        return new Thunk.More(
                () -> tryEVar(pat, pi, pe, key, newConsumed, newRemaining, env, cont));
    }

    // Сопоставление одного терма; при успехе вызывает cont. При скобках —
    // передаёт cont во внутренний rec, чтобы backtracking уходил вглубь.
    private static Thunk matchSingleAll(
            Term p, Term x, Bindings env,
            Function<Bindings, Thunk> cont) {

        if (p instanceof Var v) {
            String key = v.key();
            if (v instanceof SVar) {
                if (x instanceof Br) {
                    return new Thunk.Done(Optional.empty());
                }
                if (env.contains(key)) {
                    Expr<Term> bound = env.get(key);
                    if (bound.size() != 1 || !singleEquals(bound, x)) {
                        return new Thunk.Done(Optional.empty());
                    }
                    return cont.apply(env);
                }
                return cont.apply(env.with(key, Expr.singleton(x)));
            }
            if (v instanceof TVar) {
                if (env.contains(key)) {
                    Expr<Term> bound = env.get(key);
                    if (bound.size() != 1 || !singleEquals(bound, x)) {
                        return new Thunk.Done(Optional.empty());
                    }
                    return cont.apply(env);
                }
                return cont.apply(env.with(key, Expr.singleton(x)));
            }
            return new Thunk.Done(Optional.empty());
        }
        if (p instanceof Br pBr) {
            if (!(x instanceof Br xBr)) {
                return new Thunk.Done(Optional.empty());
            }
            List<Term> innerPat = pBr.items().toList();
            return new Thunk.More(
                    () -> rec(innerPat, 0, innerPat.size(), xBr.items(), env, cont));
        }
        // Литералы.
        return p.equals(x) ? cont.apply(env) : new Thunk.Done(Optional.empty());
    }

    private static boolean singleEquals(Expr<Term> bound, Term x) {
        Iterator<Term> it = bound.iterator();
        return it.hasNext() && it.next().equals(x);
    }

    private static Expr<Term> takeFront(Expr<Term> e, int n) {
        Expr<Term> out = Expr.empty();
        Expr<Term> cur = e;
        for (int i = 0; i < n; i++) {
            PeekResult<Term> pr = cur.separateFront();
            out = out.pushBack(pr.term());
            cur = pr.rest();
        }
        return out;
    }

    private static Expr<Term> dropFront(Expr<Term> e, int n) {
        Expr<Term> cur = e;
        for (int i = 0; i < n; i++) {
            cur = cur.separateFront().rest();
        }
        return cur;
    }
}
