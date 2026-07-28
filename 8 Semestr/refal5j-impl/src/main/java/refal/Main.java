package refal;

import refal.ast.AstFormatter;
import refal.ast.Br;
import refal.ast.Call;
import refal.ast.Func;
import refal.ast.Program;
import refal.ast.Rule;
import refal.ast.Sym;
import refal.ast.Term;
import refal.lexer.LexException;
import refal.parser.ParseException;
import refal.parser.Parser;
import refal.runtime.Builtins;
import refal.runtime.RefalException;
import refal.runtime.Runtime;
import refal.semantic.SemanticChecker;
import refal.semantic.SemanticException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;

/**
 * CLI-обёртка интерпретатора Рефала-5.
 *
 * java -jar refal5q.jar file.ref; [--entry Name] [--step-limit N] [--expr "...arguments..."]
 */
public final class Main {

    private Main() {
    }

    public static void main(String[] args) {
        int code = run(args, System.out, System.err);
        System.exit(code);
    }

    /** Чистая версия CLI — для интеграционного тестирования без System.exit. */
    public static int run(String[] args, java.io.PrintStream out, java.io.PrintStream err) {
        Args parsed;
        try {
            parsed = Args.parse(args);
        } catch (IllegalArgumentException e) {
            err.println("[ERROR] " + e.getMessage());
            err.println(USAGE);
            return 1;
        }
        if (parsed == null) {
            out.println(USAGE);
            return 0;
        }

        // Поддержка нескольких файлов через '+': main.ref+lib1.ref+lib2.ref
        // Каждый файл парсится отдельно, затем программы сливаются.
        // Публичные функции помечаются $ENTRY — их имена остаются стабильными
        // и доступны из других файлов. Приватные (без $ENTRY) получают
        // уникальный префикс по имени файла — это исключает коллизии имён
        // между внутренними вспомогательными функциями разных модулей.
        String[] files = parsed.file.split("\\+");
        Program program = null;
        for (String f : files) {
            if (f.isEmpty()) {
                continue;
            }
            String src;
            try {
                src = Files.readString(Path.of(f), StandardCharsets.UTF_8);
            } catch (IOException e) {
                err.println("[ERROR] cannot read " + f + ": " + e.getMessage());
                return 1;
            }
            Program part;
            try {
                part = Parser.parse(src);
            } catch (LexException | ParseException e) {
                err.println("[ERROR] " + f + ":" + e.getMessage());
                return 1;
            }
            if (files.length > 1) {
                part = mangleModule(part, modulePrefix(f), src);
            }
            program = (program == null) ? part : mergePrograms(program, part);
        }
        if (program == null) {
            err.println("[ERROR] no source files specified");
            return 1;
        }

        List<Term> initial;
        try {
            initial = parsed.expr.isEmpty()
                    ? List.of()
                    : Parser.parseTerms(parsed.expr);
        } catch (LexException | ParseException e) {
            err.println("[ERROR] --expr: " + e.getMessage());
            return 1;
        }

        Runtime rt = new Runtime(program, Builtins.defaultBuiltins(), parsed.stepLimit);
        // По соглашению Рефала-5 <Arg 0> — это «имя программы», поэтому
        // пользовательские аргументы доступны начиная с <Arg 1>.
        String[] argv = new String[parsed.programArgs.length + 1];
        argv[0] = "refal5q";
        System.arraycopy(parsed.programArgs, 0, argv, 1, parsed.programArgs.length);
        rt.setProgramArgs(argv);

        Optional<String> overrideEntry = parsed.entry == null
                ? Optional.empty()
                : Optional.of(parsed.entry);
        try {
            SemanticChecker.check(program, overrideEntry, rt.builtinNames());
        } catch (SemanticException e) {
            err.println("[ERROR] " + parsed.file + ": " + e.getMessage());
            return 1;
        }

        final Program prog = program;
        String entry = overrideEntry.orElseGet(() -> prog.entry().orElse(null));
        if (entry == null) {
            err.println("[ERROR] " + parsed.file
                    + ": no $ENTRY in program and no --entry specified");
            return 1;
        }

        try {
            List<Term> result = rt.run(entry, initial);
            String stdout = rt.stdout();
            if (!stdout.isEmpty()) {
                out.print(stdout);
                if (!stdout.endsWith("\n")) {
                    out.println();
                }
            }
            flushStderr(rt, err);
            String formatted = AstFormatter.format(result);
            if (!formatted.isEmpty()) {
                out.println(formatted);
            }
            return 0;
        } catch (Builtins.ExitSignal exit) {
            String stdout = rt.stdout();
            if (!stdout.isEmpty()) {
                out.print(stdout);
            }
            flushStderr(rt, err);
            return exit.code();
        } catch (RefalException e) {
            String stdout = rt.stdout();
            if (!stdout.isEmpty()) {
                out.print(stdout);
            }
            flushStderr(rt, err);
            err.println("[ERROR] runtime: " + e.getMessage());
            return 2;
        }
    }

    private static void flushStderr(Runtime rt, java.io.PrintStream err) {
        String s = rt.stderr();
        if (!s.isEmpty()) {
            err.print(s);
        }
    }

    /**
     * Сливает программу b в a: функции из b, отсутствующие в a, добавляются;
     * совпадающие имена молча игнорируются (a — приоритетнее). $ENTRY
     * наследуется от a, если задана; иначе берётся из b. $EXTERN объединяются.
     */
    private static Program mergePrograms(Program a, Program b) {
        Program.Builder builder = Program.builder();
        for (var e : a.funcs().entrySet()) {
            builder.addFunc(e.getValue());
        }
        for (var e : b.funcs().entrySet()) {
            if (!builder.hasFunc(e.getKey())) {
                builder.addFunc(e.getValue());
            }
        }
        builder.addExterns(new java.util.ArrayList<>(a.externs()));
        builder.addExterns(new java.util.ArrayList<>(b.externs()));
        if (a.entry().isPresent()) {
            builder.entry(a.entry().get());
        } else if (b.entry().isPresent()) {
            builder.entry(b.entry().get());
        }
        return builder.build();
    }

    private static final java.util.regex.Pattern ENTRY_NAME_RE =
            java.util.regex.Pattern.compile("\\$ENTRY\\s+([A-Za-z][\\w.+\\-]*)");

    private static String modulePrefix(String filepath) {
        String base = filepath.replace('\\', '/');
        int slash = base.lastIndexOf('/');
        if (slash >= 0) {
            base = base.substring(slash + 1);
        }
        int dot = base.lastIndexOf('.');
        if (dot >= 0) {
            base = base.substring(0, dot);
        }
        if (base.endsWith("_desugared")) {
            base = base.substring(0, base.length() - "_desugared".length());
        }
        return base.toLowerCase() + "_";
    }

    // Переименовывает приватные (не-$ENTRY) функции модуля с заданным префиксом,
    // чтобы избежать коллизий при слиянии нескольких файлов. Публичные функции
    // ($ENTRY) остаются с прежними именами и доступны из других модулей.
    private static Program mangleModule(Program p, String prefix, String source) {
        java.util.Set<String> entries = new java.util.HashSet<>();
        var m = ENTRY_NAME_RE.matcher(source);
        while (m.find()) {
            entries.add(m.group(1));
        }
        java.util.Set<String> used = new java.util.HashSet<>(p.funcs().keySet());
        java.util.Map<String, String> rename = new java.util.HashMap<>();
        for (String fname : p.funcs().keySet()) {
            if (entries.contains(fname)) {
                continue;
            }
            String cand = prefix + fname;
            while (used.contains(cand)) {
                cand = cand + "_";
            }
            rename.put(fname, cand);
            used.add(cand);
        }

        Program.Builder b = Program.builder();
        for (Func f : p.funcs().values()) {
            String newName = rename.getOrDefault(f.name(), f.name());
            java.util.List<Rule> newRules = new java.util.ArrayList<>();
            for (Rule r : f.rules()) {
                newRules.add(new Rule(
                        rewriteTerms(r.pattern(), rename),
                        rewriteTerms(r.result(), rename)));
            }
            b.addFunc(new Func(newName, newRules));
        }
        b.addExterns(new java.util.ArrayList<>(p.externs()));
        p.entry().ifPresent(b::entry);
        return b.build();
    }

    private static java.util.List<Term> rewriteTerms(
            java.util.List<Term> terms, java.util.Map<String, String> rename) {
        java.util.List<Term> out = new java.util.ArrayList<>(terms.size());
        for (Term t : terms) {
            out.add(rewriteTerm(t, rename));
        }
        return out;
    }

    private static Term rewriteTerm(Term t, java.util.Map<String, String> rename) {
        if (t instanceof Call c) {
            String newFn = rename.getOrDefault(c.fn(), c.fn());
            return new Call(newFn, refal.deque.Expr.fromList(rewriteTerms(c.args().toList(), rename)));
        }
        if (t instanceof Br br) {
            return new Br(refal.deque.Expr.fromList(rewriteTerms(br.items().toList(), rename)));
        }
        if (t instanceof Sym s) {
            String mapped = rename.get(s.name());
            if (mapped != null) {
                return new Sym(mapped);
            }
        }
        return t;
    }

    private static final String USAGE = String.join("\n",
            "usage:",
            "  refal5q <file.ref>[+lib.ref...] [--entry Name] [--step-limit N] [--expr \"args...\"]",
            "",
            "options:",
            "  --entry Name        override $ENTRY",
            "  --step-limit N      limit normalisation steps (default 100000)",
            "  --expr \"...\"        pass an expression as the entry argument",
            "");

    /** Простой парсер аргументов (без зависимостей). */
    static final class Args {
        String file;
        String entry;
        int stepLimit = Runtime.DEFAULT_STEP_LIMIT;
        String expr = "";
        String[] programArgs = new String[0];

        static Args parse(String[] args) {
            if (args.length == 0
                    || (args.length == 1 && (args[0].equals("-h") || args[0].equals("--help")))) {
                return null;
            }
            Args a = new Args();
            int i = 0;
            while (i < args.length) {
                String s = args[i];
                switch (s) {
                    case "--entry" -> {
                        if (++i >= args.length) {
                            throw new IllegalArgumentException("--entry requires an argument");
                        }
                        a.entry = args[i++];
                    }
                    case "--step-limit" -> {
                        if (++i >= args.length) {
                            throw new IllegalArgumentException("--step-limit requires an argument");
                        }
                        try {
                            a.stepLimit = Integer.parseInt(args[i++]);
                        } catch (NumberFormatException nfe) {
                            throw new IllegalArgumentException("--step-limit: not a number");
                        }
                    }
                    case "--expr" -> {
                        if (++i >= args.length) {
                            throw new IllegalArgumentException("--expr requires an argument");
                        }
                        a.expr = args[i++];
                    }
                    default -> {
                        if (s.startsWith("--")) {
                            throw new IllegalArgumentException("unknown option: " + s);
                        }
                        if (a.file == null) {
                            a.file = s;
                            i++;
                        } else {
                            // Все позиционные после файла — аргументы программы Рефала.
                            java.util.ArrayList<String> rest = new java.util.ArrayList<>();
                            while (i < args.length) {
                                rest.add(args[i++]);
                            }
                            a.programArgs = rest.toArray(new String[0]);
                        }
                    }
                }
            }
            if (a.file == null) {
                throw new IllegalArgumentException("missing source file");
            }
            return a;
        }
    }
}
