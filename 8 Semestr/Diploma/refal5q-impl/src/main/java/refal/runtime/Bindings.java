package refal.runtime;

import refal.ast.Term;
import refal.deque.Expr;

import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

// Окружение сопоставления: ключ переменной (вида "s.X") -> последовательность термов.
// Значения хранятся как Expr (деки), поэтому «копирование» переменной — O(1).
public final class Bindings {

    private final Map<String, Expr<Term>> map;

    private Bindings(Map<String, Expr<Term>> map) {
        this.map = map;
    }

    public static Bindings empty() {
        return new Bindings(new LinkedHashMap<>());
    }

    public boolean contains(String key) {
        return map.containsKey(key);
    }

    public Expr<Term> get(String key) {
        return map.get(key);
    }

    public Bindings with(String key, Expr<Term> value) {
        Map<String, Expr<Term>> next = new LinkedHashMap<>(map);
        next.put(key, value);
        return new Bindings(next);
    }

    // Удобная перегрузка для тестов: принимает обычный List.
    public Bindings with(String key, List<Term> value) {
        return with(key, Expr.fromList(value));
    }

    public Map<String, Expr<Term>> asMap() {
        return Map.copyOf(map);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Bindings b)) {
            return false;
        }
        if (!map.keySet().equals(b.map.keySet())) {
            return false;
        }
        for (var e : map.entrySet()) {
            if (!equalExprs(e.getValue(), b.map.get(e.getKey()))) {
                return false;
            }
        }
        return true;
    }

    @Override
    public int hashCode() {
        int h = 0;
        for (var e : map.entrySet()) {
            h += Objects.hashCode(e.getKey()) ^ exprHash(e.getValue());
        }
        return h;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("Bindings{");
        boolean first = true;
        for (var e : map.entrySet()) {
            if (!first) {
                sb.append(", ");
            }
            first = false;
            sb.append(e.getKey()).append('=').append(e.getValue().toList());
        }
        return sb.append('}').toString();
    }

    // Структурное равенство двух выражений по итератору.
    public static boolean equalExprs(Expr<Term> a, Expr<Term> b) {
        if (a.size() != b.size()) {
            return false;
        }
        Iterator<Term> ia = a.iterator();
        Iterator<Term> ib = b.iterator();
        while (ia.hasNext()) {
            if (!Objects.equals(ia.next(), ib.next())) {
                return false;
            }
        }
        return true;
    }

    private static int exprHash(Expr<Term> e) {
        int h = 1;
        for (Term t : e) {
            h = 31 * h + Objects.hashCode(t);
        }
        return h;
    }

}
