package refal.semantic;

import refal.ast.Br;
import refal.ast.Call;
import refal.ast.Func;
import refal.ast.Program;
import refal.ast.Rule;
import refal.ast.Term;
import refal.ast.Var;

import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

// Семантические проверки: уникальность функций, запрет вызовов в образцах,
// типы переменных, несвязанные переменные в правой части, неизвестные вызовы.
public final class SemanticChecker {

    private SemanticChecker() {
    }

    public static SemanticInfo check(
            Program prog,
            Optional<String> overrideEntry,
            Set<String> builtinNames) {
        Set<String> bins = builtinNames == null ? Set.of() : builtinNames;

        // 1. дубли определений функций — Program.Builder уже собрал их.
        if (!prog.duplicateFuncNames().isEmpty()) {
            String name = prog.duplicateFuncNames().iterator().next();
            throw new SemanticException(
                    SemanticException.Kind.DUPLICATE_FUNCTION,
                    "duplicate function definition: '" + name + "'",
                    name, -1);
        }

        Map<String, Func> funcEnv = new HashMap<>(prog.funcs());

        // 1b. Конфликт имени пользовательской функции со встроенной.
        for (String funcName : funcEnv.keySet()) {
            if (bins.contains(funcName)) {
                throw new SemanticException(
                        SemanticException.Kind.BUILTIN_SHADOW,
                        "function '" + funcName + "' shadows a built-in with the same name",
                        funcName, -1);
            }
        }

        // 2. вызываемые имена: user funcs + externs + builtins
        Set<String> callable = new HashSet<>();
        callable.addAll(funcEnv.keySet());
        callable.addAll(prog.externs());
        callable.addAll(bins);

        for (Func f : funcEnv.values()) {
            int ruleIdx = 0;
            for (Rule r : f.rules()) {
                checkNoCallInPattern(f.name(), ruleIdx, r.pattern());

                Map<String, Character> patternVars = new HashMap<>();
                collectPatternVarKinds(r.pattern(), patternVars, f.name(), ruleIdx);

                checkResultVars(r.result(), patternVars, f.name(), ruleIdx);
                checkCalls(r.result(), callable, f.name(), ruleIdx);

                ruleIdx++;
            }
        }

        // 3. entry resolution
        Optional<String> effectiveEntry =
                overrideEntry.or(prog::entry);
        if (effectiveEntry.isPresent()
                && !funcEnv.containsKey(effectiveEntry.get())) {
            throw new SemanticException(
                    SemanticException.Kind.UNDEFINED_ENTRY,
                    "Entry function '" + effectiveEntry.get()
                            + "' is not defined in the program",
                    effectiveEntry.get(), -1);
        }

        Set<String> externsLinked = new LinkedHashSet<>(prog.externs());
        return new SemanticInfo(funcEnv, externsLinked, effectiveEntry, bins);
    }

    private static void checkNoCallInPattern(
            String fn, int ruleIdx, Iterable<Term> pattern) {
        for (Term t : pattern) {
            if (t instanceof Call c) {
                throw new SemanticException(
                        SemanticException.Kind.CALL_IN_PATTERN,
                        "function '" + fn + "', rule #" + (ruleIdx + 1)
                                + ": call '<" + c.fn() + " ...>' is not allowed in pattern",
                        fn, ruleIdx);
            }
            if (t instanceof Br br) {
                checkNoCallInPattern(fn, ruleIdx, br.items());
            }
        }
    }

    private static void collectPatternVarKinds(
            Iterable<Term> pattern,
            Map<String, Character> out,
            String fn, int ruleIdx) {
        // В классическом Рефале-5 переменные s.X, t.X, e.X — три разных
        // переменных, даже с одинаковым именем. Поэтому ключ карты — это
        // полная пара «префикс.имя», конфликтов по совпадающему имени нет.
        for (Term t : pattern) {
            if (t instanceof Var v) {
                out.put(v.kind() + "." + v.name(), v.kind());
            } else if (t instanceof Br br) {
                collectPatternVarKinds(br.items(), out, fn, ruleIdx);
            }
        }
    }

    private static void checkResultVars(
            Iterable<Term> result,
            Map<String, Character> patternVars,
            String fn, int ruleIdx) {
        for (Term t : result) {
            switch (t) {
                case Var v -> {
                    String key = v.kind() + "." + v.name();
                    if (!patternVars.containsKey(key)) {
                        throw new SemanticException(
                                SemanticException.Kind.UNBOUND_VARIABLE,
                                "function '" + fn + "', rule #" + (ruleIdx + 1)
                                        + ": variable " + v.kind() + "." + v.name()
                                        + " in result is not bound in pattern",
                                fn, ruleIdx);
                    }
                }
                case Br br -> checkResultVars(br.items(), patternVars, fn, ruleIdx);
                case Call c -> checkResultVars(c.args(), patternVars, fn, ruleIdx);
                default -> { /* атомарный — пропускаем */ }
            }
        }
    }

    private static void checkCalls(
            Iterable<Term> result,
            Set<String> known,
            String fn, int ruleIdx) {
        for (Term t : result) {
            if (t instanceof Call c) {
                if (!known.contains(c.fn())) {
                    throw new SemanticException(
                            SemanticException.Kind.UNDEFINED_FUNCTION,
                            "function '" + fn + "', rule #" + (ruleIdx + 1)
                                    + ": call to undefined function '" + c.fn() + "'",
                            fn, ruleIdx);
                }
                checkCalls(c.args(), known, fn, ruleIdx);
            } else if (t instanceof Br br) {
                checkCalls(br.items(), known, fn, ruleIdx);
            }
        }
    }
}
