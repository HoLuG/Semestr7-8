package refal.runtime;

import refal.ast.Br;
import refal.ast.Call;
import refal.ast.Func;
import refal.ast.Program;
import refal.ast.Rule;
import refal.ast.Term;
import refal.deque.Expr;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

// Интерпретатор базисного подмножества Рефала-5.
// Аргументы функций передаются как деки термов (Expr<Term>).
public final class Runtime {

    public static final int DEFAULT_STEP_LIMIT = 100_000;

    private final Program program;
    private final Map<String, BuiltinFn> builtins;
    private final int stepLimit;
    private final StringBuilder stdout = new StringBuilder();
    private final StringBuilder stderr = new StringBuilder();
    private int steps;
    private String[] programArgs = new String[0];
    private final Map<Long, BufferedReader> openReaders = new HashMap<>();
    private final Map<Long, BufferedWriter> openWriters = new HashMap<>();
    private long startNanos = System.nanoTime();
    private BufferedReader stdinReader;

    public Runtime(Program program) {
        this(program, Builtins.defaultBuiltins(), DEFAULT_STEP_LIMIT);
    }

    public Runtime(Program program, Map<String, BuiltinFn> builtins, int stepLimit) {
        this.program = program;
        this.builtins = new LinkedHashMap<>(builtins);
        if (stepLimit <= 0) {
            throw new IllegalArgumentException("stepLimit must be > 0");
        }
        this.stepLimit = stepLimit;
    }

    public String stdout() {
        return stdout.toString();
    }

    public String stderr() {
        return stderr.toString();
    }

    void appendStdout(String s) {
        stdout.append(s);
    }

    void appendStderr(String s) {
        stderr.append(s);
    }

    public Set<String> builtinNames() {
        return builtins.keySet();
    }

    public void setProgramArgs(String[] args) {
        this.programArgs = args == null ? new String[0] : args.clone();
    }

    String[] programArgs() {
        return programArgs;
    }

    /** Текущее число выполненных шагов нормализации. */
    int currentStep() {
        return steps;
    }

    /** Время от запуска интерпретатора, в секундах. */
    double timeElapsedSeconds() {
        return (System.nanoTime() - startNanos) / 1_000_000_000.0;
    }

    /** Сброс таймера (для <TimeElapsed 0>). */
    void resetStartNanos() {
        startNanos = System.nanoTime();
    }

    void openFile(long channel, String mode, String filename) {
        try {
            closeChannel(channel);
            switch (mode.toLowerCase(java.util.Locale.ROOT)) {
                case "r" -> {
                    BufferedReader r = Files.newBufferedReader(
                            Paths.get(filename), StandardCharsets.UTF_8);
                    openReaders.put(channel, r);
                }
                case "w" -> {
                    BufferedWriter w = Files.newBufferedWriter(
                            Paths.get(filename), StandardCharsets.UTF_8);
                    openWriters.put(channel, w);
                }
                case "a" -> {
                    BufferedWriter w = Files.newBufferedWriter(
                            Paths.get(filename), StandardCharsets.UTF_8,
                            StandardOpenOption.CREATE, StandardOpenOption.APPEND);
                    openWriters.put(channel, w);
                }
                default -> throw new RefalException(
                        "Open: unknown mode '" + mode + "' (expected r/w/a)");
            }
        } catch (IOException e) {
            throw new RefalException("Open: I/O error: " + e.getMessage());
        }
    }

    void closeFile(long channel) {
        try {
            closeChannel(channel);
        } catch (IOException e) {
            throw new RefalException("Close: I/O error: " + e.getMessage());
        }
    }

    private void closeChannel(long channel) throws IOException {
        Closeable r = openReaders.remove(channel);
        Closeable w = openWriters.remove(channel);
        if (r != null) {
            r.close();
        }
        if (w != null) {
            w.close();
        }
    }

    String readFileLine(long channel) {
        if (!openReaders.containsKey(channel)) {
            // Традиционный Рефал-5: автооткрытие REFALNN.DAT для чтения.
            openFile(channel, "r", defaultChannelFile(channel));
        }
        BufferedReader r = openReaders.get(channel);
        try {
            return r.readLine();
        } catch (IOException e) {
            throw new RefalException("Get: I/O error: " + e.getMessage());
        }
    }

    String readStdinLine() {
        // Блокируемся в ожидании строки — иначе тесты с piped-stdin падают
        // на Windows: System.in.available() для канала из pipe возвращает 0
        // даже когда данные уже доступны.
        try {
            if (stdinReader == null) {
                stdinReader = new BufferedReader(
                        new InputStreamReader(System.in, StandardCharsets.UTF_8));
            }
            return stdinReader.readLine();
        } catch (IOException e) {
            return null;
        }
    }

    private static String defaultChannelFile(long ch) {
        return String.format("REFAL%02d.DAT", ch);
    }

    void writeFile(long channel, String text) {
        // Канал 0 — поток ошибок (stderr).
        if (channel == 0) {
            appendStderr(text);
            return;
        }
        if (!openWriters.containsKey(channel)) {
            // Автооткрытие REFALNN.DAT в режиме добавления.
            openFile(channel, "a", defaultChannelFile(channel));
        }
        BufferedWriter w = openWriters.get(channel);
        try {
            w.write(text);
            w.flush();
        } catch (IOException e) {
            throw new RefalException("Put: I/O error: " + e.getMessage());
        }
    }

    private void closeAllFiles() {
        for (var r : openReaders.values()) {
            try {
                r.close();
            } catch (IOException ignored) {
                // закрываем по возможности, ошибки игнорируем
            }
        }
        for (var w : openWriters.values()) {
            try {
                w.close();
            } catch (IOException ignored) {
                // закрываем по возможности, ошибки игнорируем
            }
        }
        openReaders.clear();
        openWriters.clear();
    }

    public Expr<Term> evalCall(String fn, List<Term> args) {
        return evalCall(fn, Expr.fromList(args));
    }

    // Применить функцию к аргументам (одно применение, без нормализации).
    public Expr<Term> evalCall(String fn, Expr<Term> args) {
        BuiltinFn b = builtins.get(fn);
        if (b != null) {
            return b.apply(this, args);
        }
        Optional<Func> f = program.getFunc(fn);
        if (f.isEmpty()) {
            throw new RefalException("Unknown function: " + fn);
        }
        for (Rule rule : f.get().rules()) {
            var bindings = Matcher.match(rule.pattern(), args);
            if (bindings.isPresent()) {
                return Substitutor.substitute(rule.result(), bindings.get());
            }
        }
        throw new RefalException(
                "No matching rule for " + fn + " on args=" + args.toList());
    }

    // Полная нормализация выражения через два стека (поле зрения).
    // Правый стек — необработанное выражение, левый — уже пассивные термы.
    public Expr<Term> normalize(Expr<Term> expr) {
        java.util.ArrayDeque<ViewTerm> left = new java.util.ArrayDeque<>();
        java.util.ArrayDeque<ViewTerm> right = new java.util.ArrayDeque<>();

        // Заполняем правый стек слева-направо.
        for (Term t : expr) {
            flattenInto(t, right);
        }

        while (!right.isEmpty()) {
            ViewTerm v = right.pollFirst();
            switch (v) {
                case ViewTerm.Passive p -> left.addLast(p);
                case ViewTerm.BulkPassive bp -> left.addLast(bp);
                case ViewTerm.AngOpen open -> left.addLast(open);
                case ViewTerm.ParenOpen open -> left.addLast(open);

                case ViewTerm.ParenClose ignored -> {
                    // Свернуть верх left до ParenOpen в скобочный терм.
                    // Элементы собираются справа-налево (pollLast), поэтому
                    // одиночный Passive добавляется pushFront, а BulkPassive — concat слева.
                    Expr<Term> brItems = Expr.empty();
                    while (true) {
                        ViewTerm top = left.pollLast();
                        if (top == null) {
                            throw new RefalException("Unmatched ')' in view field");
                        }
                        if (top instanceof ViewTerm.ParenOpen) {
                            break;
                        }
                        if (top instanceof ViewTerm.Passive pt) {
                            brItems = brItems.pushFront(pt.term());
                        } else if (top instanceof ViewTerm.BulkPassive bp) {
                            brItems = Expr.concat(bp.items(), brItems);
                        } else {
                            throw new RefalException(
                                    "Unexpected " + top + " inside brackets");
                        }
                    }
                    left.addLast(new ViewTerm.Passive(new Br(brItems)));
                }

                case ViewTerm.AngClose ignored -> {
                    bumpStep();
                    // Собрать аргументы со стека до AngOpen(fn).
                    // Элементы собираются справа-налево (pollLast): Passive → pushFront,
                    // BulkPassive → concat(items, acc) — всё O(1) амортизированно.
                    Expr<Term> argsExpr = Expr.empty();
                    String fn = null;
                    while (true) {
                        ViewTerm top = left.pollLast();
                        if (top == null) {
                            throw new RefalException("Unmatched '>' in view field");
                        }
                        if (top instanceof ViewTerm.AngOpen ao) {
                            fn = ao.fn();
                            break;
                        }
                        if (top instanceof ViewTerm.Passive pt) {
                            argsExpr = argsExpr.pushFront(pt.term());
                        } else if (top instanceof ViewTerm.BulkPassive bp) {
                            argsExpr = Expr.concat(bp.items(), argsExpr);
                        } else {
                            throw new RefalException(
                                    "Unexpected " + top + " inside <" + "...>");
                        }
                    }

                    BuiltinFn b = builtins.get(fn);
                    if (b != null) {
                        // Встроенная функция: возвращает пассивный Expr<Term>
                        // (без вызовов внутри) — сплющиваем в ViewTerm через flattenInto.
                        Expr<Term> result = b.apply(this, argsExpr);
                        java.util.ArrayDeque<ViewTerm> tmp = new java.util.ArrayDeque<>();
                        for (Term t : result) {
                            flattenInto(t, tmp);
                        }
                        java.util.Iterator<ViewTerm> it = tmp.descendingIterator();
                        while (it.hasNext()) {
                            right.addFirst(it.next());
                        }
                    } else {
                        // Пользовательская функция: кладём правую часть правила
                        // напрямую на правый стек (никаких конкатенаций и Expr с Call).
                        Optional<Func> f = program.getFunc(fn);
                        if (f.isEmpty()) {
                            throw new RefalException("Unknown function: " + fn);
                        }
                        boolean matched = false;
                        for (Rule rule : f.get().rules()) {
                            var bindings = Matcher.match(rule.pattern(), argsExpr);
                            if (bindings.isPresent()) {
                                pushResultToStack(rule.result(), bindings.get(), right);
                                matched = true;
                                break;
                            }
                        }
                        if (!matched) {
                            throw new RefalException(
                                    "No matching rule for " + fn
                                    + " on args=" + argsExpr.toList());
                        }
                    }
                }
            }
        }

        // Собрать пассивные термы из левого стека.
        Expr<Term> out = Expr.empty();
        for (ViewTerm v : left) {
            switch (v) {
                case ViewTerm.Passive p -> out = out.pushBack(p.term());
                case ViewTerm.BulkPassive bp -> out = Expr.concat(out, bp.items());
                default -> throw new RefalException(
                        "Unbalanced view field: leftover " + v);
            }
        }
        return out;
    }

    /**
     * Кладёт правую часть правила (после подстановки связываний) на правый стек
     * справа-налево: первый терм окажется на вершине стека и будет обработан первым.
     * Никаких промежуточных Expr<Term> с Call-нодами не создаётся.
     */
    private static void pushResultToStack(
            List<Term> result,
            Bindings bindings,
            java.util.ArrayDeque<ViewTerm> right) {
        for (int i = result.size() - 1; i >= 0; i--) {
            pushTermToStack(result.get(i), bindings, right);
        }
    }

    /**
     * Кладёт один терм правой части (с раскрытием переменных) на правый стек.
     * Порядок обхода: справа-налево внутри составных термов.
     */
    private static void pushTermToStack(
            Term t,
            Bindings bindings,
            java.util.ArrayDeque<ViewTerm> right) {
        switch (t) {
            case refal.ast.Var v -> {
                // Значение переменной — всегда пассивное выражение.
                // Кладём на стек одним BulkPassive (O(1)) вместо O(n) Passive-объектов.
                Expr<Term> val = bindings.get(v.key());
                if (!val.isEmpty()) {
                    right.addFirst(new ViewTerm.BulkPassive(val));
                }
            }
            case refal.ast.Br br -> {
                right.addFirst(ViewTerm.ParenClose.INSTANCE);
                List<Term> items = br.items().toList();
                for (int j = items.size() - 1; j >= 0; j--) {
                    pushTermToStack(items.get(j), bindings, right);
                }
                right.addFirst(ViewTerm.ParenOpen.INSTANCE);
            }
            case refal.ast.Call c -> {
                right.addFirst(ViewTerm.AngClose.INSTANCE);
                List<Term> cargs = c.args().toList();
                for (int j = cargs.size() - 1; j >= 0; j--) {
                    pushTermToStack(cargs.get(j), bindings, right);
                }
                right.addFirst(new ViewTerm.AngOpen(c.fn()));
            }
            default -> right.addFirst(new ViewTerm.Passive(t));
        }
    }

    /** Сплющивание AST-терма в линейную последовательность ViewTerm. */
    private static void flattenInto(Term t, java.util.ArrayDeque<ViewTerm> out) {
        switch (t) {
            case Call c -> {
                out.addLast(new ViewTerm.AngOpen(c.fn()));
                for (Term a : c.args()) {
                    flattenInto(a, out);
                }
                out.addLast(ViewTerm.AngClose.INSTANCE);
            }
            case Br br -> {
                out.addLast(ViewTerm.ParenOpen.INSTANCE);
                for (Term a : br.items()) {
                    flattenInto(a, out);
                }
                out.addLast(ViewTerm.ParenClose.INSTANCE);
            }
            default -> out.addLast(new ViewTerm.Passive(t));
        }
    }

    private void bumpStep() {
        steps++;
        if (steps > stepLimit) {
            throw new RefalException("Step limit exceeded (" + stepLimit + ")");
        }
    }

    public List<Term> run(String entry, List<Term> initial) {
        // Entry-вызов (Go) не должен учитываться как шаг нормализации.
        // bumpStep() инкрементит steps перед первой редукцией, поэтому
        // начинаем с -1: после входа в Go steps = 0, первый внутренний
        // вызов делает <Step> = 1.
        steps = -1;
        try {
            Expr<Term> initialCall = Expr.singleton(new Call(entry, Expr.fromList(initial)));
            return normalize(initialCall).toList();
        } finally {
            closeAllFiles();
        }
    }

    public List<Term> runEntry(List<Term> initial) {
        String entry = program.entry().orElseThrow(() ->
                new RefalException("Program has no $ENTRY and no entry was specified"));
        return run(entry, initial);
    }
}
