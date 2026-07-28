package refal.runtime;

import refal.ast.AstFormatter;
import refal.ast.Br;
import refal.ast.Num;
import refal.ast.Str;
import refal.ast.Sym;
import refal.ast.Term;
import refal.deque.Expr;
import refal.deque.PeekResult;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// Встроенные функции Рефала-5. Все принимают и возвращают Expr<Term>.
public final class Builtins {

    private Builtins() {
    }

    // Специальный сигнал для нормального завершения программы.
    public static final String EXIT_SIGNAL = "refal.runtime.Builtins.EXIT_SIGNAL";

    public static Map<String, BuiltinFn> defaultBuiltins() {
        Map<String, BuiltinFn> m = new LinkedHashMap<>();
        m.put("Prout", Builtins::prout);
        m.put("Print", Builtins::print);
        m.put("Putout", Builtins::putout);
        m.put("Exit", Builtins::exit);

        m.put("Add", Builtins::add);
        m.put("+", Builtins::add);
        m.put("Sub", Builtins::sub);
        m.put("-", Builtins::sub);
        m.put("Mul", Builtins::mul);
        m.put("*", Builtins::mul);
        m.put("Div", Builtins::div);
        m.put("/", Builtins::div);
        m.put("Mod", Builtins::mod);
        m.put("%", Builtins::mod);
        m.put("Divmod", Builtins::divmod);
        m.put("Compare", Builtins::compare);

        m.put("Lower", Builtins::lower);
        m.put("Upper", Builtins::upper);
        m.put("Symb", Builtins::symb);
        m.put("Numb", Builtins::numb);
        m.put("Chr", Builtins::chr);
        m.put("Ord", Builtins::ord);

        m.put("Mu", Builtins::mu);
        m.put("?", Builtins::mu);
        m.put("Residue", Builtins::mu);

        m.put("Lenw", Builtins::lenw);
        m.put("First", Builtins::first);
        m.put("Last", Builtins::last);
        m.put("Explode", Builtins::explode);
        m.put("Explode_Ext", Builtins::explode);
        m.put("Implode", Builtins::implode);
        m.put("Implode_Ext", Builtins::implodeExt);
        m.put("Step", Builtins::step);
        m.put("Card", Builtins::card);
        m.put("Type", Builtins::type);
        m.put("ListOfBuiltin", Builtins::listOfBuiltin);
        m.put("Arg", Builtins::arg);
        m.put("Open", Builtins::open);
        m.put("Close", Builtins::close);
        m.put("Get", Builtins::get);
        m.put("Put", Builtins::put);
        m.put("Putout-chan", Builtins::putoutChan);
        m.put("Write", Builtins::write);
        m.put("TimeElapsed", Builtins::timeElapsed);
        // Sysfun регистрируется как заглушка, чтобы при запуске .FAIL.ref-тестов
        // получали runtime-ошибку (exit 2), а не семантическую (exit 1).
        m.put("Sysfun", Builtins::sysfun);

        return m;
    }

    // --- вспомогательные функции ---

    /** Склейка термов в строку для текстовых функций (без пробелов, для numb/explode/open). */
    static String termsToText(Expr<Term> args) {
        StringBuilder sb = new StringBuilder();
        for (Term t : args) {
            switch (t) {
                case Sym s -> sb.append(s.name());
                case Num n -> sb.append(n.value());
                case Str s -> sb.append(s.value());
                default -> sb.append(AstFormatter.format(t));
            }
        }
        return sb.toString();
    }

    /**
     * Форматирование выражения для вывода (Prout/Put/Write):
     * — Str (символьные литералы 'x'): без пробела после
     * — Sym, Num: с пробелом после
     * — Br: рекурсивно в скобках, без пробела после ')'
     */
    static String printExpr(Expr<Term> args) {
        StringBuilder sb = new StringBuilder();
        for (Term t : args) {
            switch (t) {
                case Sym s -> sb.append(s.name()).append(' ');
                case Num n -> sb.append(n.value()).append(' ');
                case Str s -> sb.append(s.value());
                case Br br -> sb.append('(').append(printExpr(br.items())).append(')');
                default    -> sb.append(AstFormatter.format(t)).append(' ');
            }
        }
        return sb.toString();
    }

    // Основание макроцифры Рефала-5: 2^32.
    static final BigInteger MACRO_BASE = BigInteger.ONE.shiftLeft(32);

    /**
     * Разбирает последовательность макроцифр (опциональный знак Str + Num термы)
     * в одно целое число произвольной точности.
     */
    static BigInteger parseMacroNum(String name, Expr<Term> expr) {
        int sign = 1;
        Expr<Term> cur = expr;
        if (!cur.isEmpty()) {
            PeekResult<Term> pr = cur.separateFront();
            if (pr.term() instanceof Str s
                    && (s.value().equals("+") || s.value().equals("-"))) {
                sign = s.value().equals("-") ? -1 : 1;
                cur = pr.rest();
            }
        }
        BigInteger result = BigInteger.ZERO;
        boolean any = false;
        for (Term t : cur) {
            if (!(t instanceof Num n)) {
                throw new RefalException(name + ": expected Num, got "
                        + AstFormatter.format(t));
            }
            result = result.multiply(MACRO_BASE).add(n.value());
            any = true;
        }
        if (!any) {
            return BigInteger.ZERO;
        }
        return sign < 0 ? result.negate() : result;
    }

    /**
     * Разбирает два арифметических аргумента из общего выражения args.
     * Первый: Br(e) | Str(sign) Num | Num.
     * Второй: всё оставшееся (опц. Str(sign) + макроцифры).
     */
    static BigInteger[] parseTwoArgs(String name, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException(name + ": missing arguments");
        }
        PeekResult<Term> pr = args.separateFront();
        Term head = pr.term();
        Expr<Term> rest = pr.rest();
        BigInteger first;
        if (head instanceof Br br) {
            first = parseMacroNum(name, br.items());
        } else if (head instanceof Str s
                && (s.value().equals("+") || s.value().equals("-"))) {
            int sign = s.value().equals("-") ? -1 : 1;
            if (rest.isEmpty()) {
                throw new RefalException(name + ": missing digit after sign");
            }
            PeekResult<Term> pr2 = rest.separateFront();
            if (!(pr2.term() instanceof Num n)) {
                throw new RefalException(name + ": expected Num after sign, got "
                        + AstFormatter.format(pr2.term()));
            }
            first = sign < 0 ? n.value().negate() : n.value();
            rest = pr2.rest();
        } else if (head instanceof Num n) {
            first = n.value();
        } else {
            throw new RefalException(name + ": invalid first arg: "
                    + AstFormatter.format(head));
        }
        BigInteger second = parseMacroNum(name, rest);
        return new BigInteger[]{first, second};
    }

    /** BigInteger -> макроцифровое выражение (опц. знак Str + Num термы, MSB вперёд). */
    static Expr<Term> bigIntToMacrodigits(BigInteger v) {
        if (v.signum() == 0) {
            return Expr.singleton(new Num(BigInteger.ZERO));
        }
        boolean negative = v.signum() < 0;
        BigInteger abs = v.abs();
        java.util.ArrayDeque<BigInteger> digits = new java.util.ArrayDeque<>();
        BigInteger cur = abs;
        while (cur.signum() > 0) {
            BigInteger[] dm = cur.divideAndRemainder(MACRO_BASE);
            digits.addFirst(dm[1]);
            cur = dm[0];
        }
        Expr<Term> out = Expr.empty();
        if (negative) {
            out = out.pushBack(new Str("-"));
        }
        for (BigInteger d : digits) {
            out = out.pushBack(new Num(d));
        }
        return out;
    }

    private static Term singleArg(String name, Expr<Term> args) {
        if (args.size() != 1) {
            throw new RefalException(name + ": expected one argument, got "
                    + AstFormatter.format(args.toList()));
        }
        return args.separateFront().term();
    }

    // --- ввод-вывод ---

    private static Expr<Term> prout(Runtime rt, Expr<Term> args) {
        rt.appendStdout(printExpr(args) + "\n");
        return Expr.empty();
    }

    /** Печатает аргумент и возвращает его без изменений (как refgo Print). */
    private static Expr<Term> print(Runtime rt, Expr<Term> args) {
        rt.appendStdout(AstFormatter.format(args.toList()) + "\n");
        return args;
    }

    private static Expr<Term> putout(Runtime rt, Expr<Term> args) {
        // Первый терм — номер канала.
        // Канал 0 — stderr, остальные — открытые файлы.
        // Для обратной совместимости со старыми тестами: если первый терм
        // не Num, печатаем всё содержимое в stdout без перевода строки.
        if (!args.isEmpty()) {
            PeekResult<Term> pr = args.separateFront();
            if (pr.term() instanceof Num n) {
                rt.writeFile(n.value().longValue(), printExpr(pr.rest()) + "\n");
                return Expr.empty();
            }
        }
        rt.appendStdout(printExpr(args));
        return Expr.empty();
    }

    /** Write — то же, что Putout, но без перевода строки. */
    private static Expr<Term> write(Runtime rt, Expr<Term> args) {
        if (!args.isEmpty()) {
            PeekResult<Term> pr = args.separateFront();
            if (pr.term() instanceof Num n) {
                rt.writeFile(n.value().longValue(), printExpr(pr.rest()));
                return Expr.empty();
            }
        }
        rt.appendStdout(printExpr(args));
        return Expr.empty();
    }

    private static Expr<Term> exit(Runtime rt, Expr<Term> args) {
        int code = 0;
        if (!args.isEmpty()) {
            Term first = args.separateFront().term();
            if (first instanceof Num n) {
                code = n.value().intValue();
            }
        }
        throw new ExitSignal(code);
    }

    // --- арифметика ---

    private static Expr<Term> add(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Add", args);
        return bigIntToMacrodigits(ab[0].add(ab[1]));
    }

    private static Expr<Term> sub(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Sub", args);
        return bigIntToMacrodigits(ab[0].subtract(ab[1]));
    }

    private static Expr<Term> mul(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Mul", args);
        return bigIntToMacrodigits(ab[0].multiply(ab[1]));
    }

    private static Expr<Term> div(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Div", args);
        if (ab[1].signum() == 0) {
            throw new RefalException("Div: division by zero");
        }
        return bigIntToMacrodigits(ab[0].divide(ab[1]));
    }

    private static Expr<Term> mod(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Mod", args);
        if (ab[1].signum() == 0) {
            throw new RefalException("Mod: modulo by zero");
        }
        return bigIntToMacrodigits(ab[0].remainder(ab[1]));
    }

    /**
     * Целочисленное деление с остатком: частное в круглых скобках,
     * следом — остаток в виде макроцифровой последовательности (без скобок).
     * Используется усечённое (truncated) деление — как в refgo.
     */
    private static Expr<Term> divmod(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Divmod", args);
        if (ab[1].signum() == 0) {
            throw new RefalException("Divmod: division by zero");
        }
        BigInteger[] qr = ab[0].divideAndRemainder(ab[1]);
        Expr<Term> quotient = bigIntToMacrodigits(qr[0]);
        Expr<Term> out = Expr.singleton(new Br(quotient));
        return Expr.concat(out, bigIntToMacrodigits(qr[1]));
    }

    private static Expr<Term> compare(Runtime rt, Expr<Term> args) {
        BigInteger[] ab = parseTwoArgs("Compare", args);
        int c = ab[0].compareTo(ab[1]);
        if (c < 0) {
            return Expr.singleton(new Str("-"));
        }
        if (c > 0) {
            return Expr.singleton(new Str("+"));
        }
        return Expr.singleton(new Str("0"));
    }

    // --- строки / символы ---

    private static Expr<Term> lower(Runtime rt, Expr<Term> args) {
        return caseFold(args, true);
    }

    private static Expr<Term> upper(Runtime rt, Expr<Term> args) {
        return caseFold(args, false);
    }

    /**
     * Применяет toLowerCase/toUpperCase к каждому символу/строке/символу-идентификатору
     * по отдельности, сохраняя структуру термов (числа/скобки — без изменений,
     * содержимое скобок рекурсивно).
     */
    private static Expr<Term> caseFold(Expr<Term> args, boolean toLower) {
        java.util.Locale loc = java.util.Locale.ROOT;
        Expr<Term> out = Expr.empty();
        for (Term t : args) {
            switch (t) {
                case Str s -> out = out.pushBack(new Str(
                        toLower ? s.value().toLowerCase(loc) : s.value().toUpperCase(loc)));
                // Sym (идентификаторы) — оставляем как есть, в refgo Lower/Upper их не трогает.
                case Br br -> out = out.pushBack(new Br(
                        caseFold(br.items(), toLower)));
                default -> out = out.pushBack(t);
            }
        }
        return out;
    }

    /**
     * Преобразует макроцифровое число в последовательность односимвольных
     * Str-термов десятичного представления (классическое поведение Symb).
     * Если в аргументе нет ни одной макроцифры — возвращает '0'.
     */
    private static Expr<Term> symb(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            return Expr.empty();
        }
        BigInteger v = parseMacroNum("Symb", args);
        String text = v.toString();
        Expr<Term> out = Expr.empty();
        for (int i = 0; i < text.length(); i++) {
            out = out.pushBack(new Str(String.valueOf(text.charAt(i))));
        }
        return out;
    }

    /**
     * Преобразует строковое десятичное представление в макроцифровую
     * последовательность. Аргумент собирается через termsToText (поддерживает
     * Str-«посимвольный» формат); пустой/невалидный вход даёт 0.
     */
    private static Expr<Term> numb(Runtime rt, Expr<Term> args) {
        String text = termsToText(args).strip();
        if (text.isEmpty()) {
            return bigIntToMacrodigits(BigInteger.ZERO);
        }
        int i = 0;
        boolean negative = false;
        if (text.charAt(0) == '+' || text.charAt(0) == '-') {
            negative = text.charAt(0) == '-';
            i = 1;
        }
        int j = i;
        while (j < text.length() && Character.isDigit(text.charAt(j))) {
            j++;
        }
        if (j == i) {
            return bigIntToMacrodigits(BigInteger.ZERO);
        }
        BigInteger v = new BigInteger(text.substring(i, j));
        if (negative) {
            v = v.negate();
        }
        return bigIntToMacrodigits(v);
    }

    /**
     * Для каждого числа заменяет его строкой с символом этого кода;
     * остальные термы (включая скобочные — рекурсивно) переносятся без изменений.
     */
    private static Expr<Term> chr(Runtime rt, Expr<Term> args) {
        Expr<Term> out = Expr.empty();
        for (Term t : args) {
            switch (t) {
                case Num n -> out = out.pushBack(new Str(
                        String.valueOf((char) (n.value().longValue() & 0xFF))));
                case Br br -> out = out.pushBack(new Br(chr(rt, br.items())));
                default -> out = out.pushBack(t);
            }
        }
        return out;
    }

    /**
     * Для каждой односимвольной строки или символа заменяет его числом — кодом символа;
     * остальные термы переносятся без изменений.
     */
    private static Expr<Term> ord(Runtime rt, Expr<Term> args) {
        Expr<Term> out = Expr.empty();
        for (Term t : args) {
            switch (t) {
                case Str s -> {
                    String v = s.value();
                    if (v.length() == 1) {
                        out = out.pushBack(new Num(v.charAt(0)));
                    } else if (v.isEmpty()) {
                        // пропускаем пустую строку
                    } else {
                        // многосимвольная строка: оставляем без изменений, чтобы
                        // тест сравнения не сопоставлял с числом, но и не падал.
                        out = out.pushBack(t);
                    }
                }
                case Sym s -> {
                    if (s.name().length() == 1) {
                        out = out.pushBack(new Num(s.name().charAt(0)));
                    } else {
                        out = out.pushBack(t);
                    }
                }
                case Br br -> out = out.pushBack(new Br(ord(rt, br.items())));
                default -> out = out.pushBack(t);
            }
        }
        return out;
    }

    /**
     * Читает строку со стандартного ввода до перевода строки;
     * при конце ввода возвращает число 0.
     */
    private static Expr<Term> card(Runtime rt, Expr<Term> args) {
        // По соглашению Рефала-5 — то же, что <Get 0>: посимвольная строка
        // или 0 при достижении EOF.
        String line = rt.readStdinLine();
        if (line == null) {
            return Expr.singleton(new Num(0));
        }
        return explodeString(line);
    }

    /**
     * Определяет тип первого терма (N — число, W — слово, L — строка, O — скобочное
     * выражение по соглашению Рефала-5), подкатегорию и исходное выражение.
     */
    private static Expr<Term> type(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            return Expr.fromList(java.util.List.of(
                    (Term) new Str("*"), new Str("0")));
        }
        PeekResult<Term> pr = args.separateFront();
        Term first = pr.term();
        Expr<Term> tail = pr.rest();
        String cat;
        String sub;
        switch (first) {
            case Num ignored -> {
                cat = "N";
                sub = "0";
            }
            case Sym s -> {
                // Идентификатор-слово: 'W' 'i' если корректный идентификатор, иначе 'W' 'q'.
                cat = "W";
                sub = isIdentifier(s.name()) ? "i" : "q";
            }
            case Str s -> {
                String v = s.value();
                if (v.length() == 1) {
                    char ch = v.charAt(0);
                    if (Character.isDigit(ch)) {
                        cat = "D";
                        sub = "0";
                    } else if (Character.isUpperCase(ch)) {
                        cat = "L";
                        sub = "u";
                    } else if (Character.isLowerCase(ch)) {
                        cat = "L";
                        sub = "l";
                    } else if (Character.isISOControl(ch)) {
                        cat = "O";
                        sub = "l";
                    } else {
                        cat = "P";
                        sub = "l";
                    }
                } else {
                    // Многосимвольная строка — слово в кавычках.
                    cat = "W";
                    sub = "q";
                }
            }
            case Br ignored -> {
                cat = "B";
                sub = "0";
            }
            default -> {
                cat = "*";
                sub = "0";
            }
        }
        Expr<Term> out = Expr.singleton((Term) new Str(cat));
        out = out.pushBack(new Str(sub));
        // Возвращаем исходный терм + хвост (исходное выражение остаётся целым).
        out = out.pushBack(first);
        return Expr.concat(out, tail);
    }

    // --- функции высшего порядка ---

    /** Применяет именованную функцию к аргументам (метапрограммирование). */
    private static Expr<Term> mu(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException("Mu: missing function name");
        }
        PeekResult<Term> pr = args.separateFront();
        String name = extractName("Mu", pr.term());
        return rt.evalCall(name, pr.rest());
    }

    private static String extractName(String fn, Term t) {
        return switch (t) {
            case Sym s -> s.name();
            case Str s -> s.value();
            case Br br -> {
                // Имя может быть «упаковано» как (Sym) либо как
                // (Str Str Str ...) — последовательность односимвольных строк
                // от 'Foo'. Склеиваем содержимое скобки в одно имя.
                StringBuilder sb = new StringBuilder();
                for (Term it : br.items()) {
                    switch (it) {
                        case Sym s -> sb.append(s.name());
                        case Str s -> sb.append(s.value());
                        default -> throw new RefalException(
                                fn + ": first argument must be a function name, got "
                                        + AstFormatter.format(t));
                    }
                }
                yield sb.toString();
            }
            default -> throw new RefalException(
                    fn + ": first argument must be a function name, got "
                            + AstFormatter.format(t));
        };
    }

    // --- операции над списками / последовательностями ---

    /** Длина выражения в начале, затем те же термы. */
    private static Expr<Term> lenw(Runtime rt, Expr<Term> args) {
        return args.pushFront(new Num(args.size()));
    }

    /** Текущее число шагов нормализации. */
    private static Expr<Term> step(Runtime rt, Expr<Term> args) {
        return Expr.singleton(new Num(rt.currentStep()));
    }

    /** Оставляет последние N термов снаружи, остальное помещает в скобки. */
    private static Expr<Term> last(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException("Last: missing count argument");
        }
        PeekResult<Term> pr = args.separateFront();
        if (!(pr.term() instanceof Num n)) {
            throw new RefalException("Last: count must be a number, got "
                    + AstFormatter.format(pr.term()));
        }
        long count = n.value().longValue();
        if (count < 0) {
            throw new RefalException("Last: negative count");
        }
        Expr<Term> rest = pr.rest();
        long total = rest.size();
        if (count > total) {
            count = total;
        }
        long headLen = total - count;
        Expr<Term> head = Expr.empty();
        Expr<Term> cur = rest;
        for (long i = 0; i < headLen; i++) {
            PeekResult<Term> step = cur.separateFront();
            head = head.pushBack(step.term());
            cur = step.rest();
        }
        Expr<Term> out = Expr.singleton(new Br(head));
        return Expr.concat(out, cur);
    }

    /**
     * Первые N термов выделяются в скобки, остальное остаётся снаружи.
     */
    private static Expr<Term> first(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException("First: missing count argument");
        }
        PeekResult<Term> pr = args.separateFront();
        if (!(pr.term() instanceof Num n)) {
            throw new RefalException("First: count must be a number, got "
                    + AstFormatter.format(pr.term()));
        }
        long count = n.value().longValue();
        if (count < 0) {
            throw new RefalException("First: negative count");
        }
        Expr<Term> rest = pr.rest();
        if (count > rest.size()) {
            count = rest.size();
        }
        Expr<Term> head = Expr.empty();
        Expr<Term> cur = rest;
        for (long i = 0; i < count; i++) {
            PeekResult<Term> step = cur.separateFront();
            head = head.pushBack(step.term());
            cur = step.rest();
        }
        Expr<Term> out = Expr.singleton(new Br(head));
        return Expr.concat(out, cur);
    }

    /** Разбивает строку на односимвольные строковые атомы. */
    private static Expr<Term> explode(Runtime rt, Expr<Term> args) {
        String text = termsToText(args);
        Expr<Term> out = Expr.empty();
        for (int i = 0; i < text.length(); i++) {
            out = out.pushBack(new Str(String.valueOf(text.charAt(i))));
        }
        return out;
    }

    /**
     * Склеивает символы и строки в один идентификатор или строку.
     */
    private static Expr<Term> implode(Runtime rt, Expr<Term> args) {
        // Собираем «головную» цепочку односимвольных Str-термов в строку,
        // остальное (нечары, скобки, числа, многосимвольные строки) добавляем
        // в результат без изменений.
        StringBuilder head = new StringBuilder();
        Expr<Term> tail = Expr.empty();
        boolean stopped = false;
        for (Term t : args) {
            if (!stopped && t instanceof Str s && s.value().length() == 1) {
                head.append(s.value().charAt(0));
            } else {
                stopped = true;
                tail = tail.pushBack(t);
            }
        }
        String text = head.toString();
        if (text.isEmpty() && tail.isEmpty()) {
            return Expr.empty();
        }
        Expr<Term> out = Expr.empty();
        if (text.isEmpty()) {
            // Чары впереди отсутствуют — возвращаем хвост как есть.
            return tail;
        }
        if (!Character.isLetter(text.charAt(0))) {
            // refgo: «0» + посимвольный хвост.
            out = out.pushBack(new Num(BigInteger.ZERO));
            for (int k = 0; k < text.length(); k++) {
                out = out.pushBack(new Str(String.valueOf(text.charAt(k))));
            }
            return Expr.concat(out, tail);
        }
        int j = 0;
        while (j < text.length() && isImplodeIdentChar(text.charAt(j))) {
            j++;
        }
        out = out.pushBack(new Sym(text.substring(0, j)));
        for (int k = j; k < text.length(); k++) {
            out = out.pushBack(new Str(String.valueOf(text.charAt(k))));
        }
        return Expr.concat(out, tail);
    }

    /**
     * Множество «идентификаторных» символов для Implode/Implode_Ext.
     * Соответствует refgo: буквы, цифры, '_', '-', '$' (и любые
     * другие неблочные печатные знаки, кроме явно перечисленных разделителей).
     */
    private static boolean isImplodeIdentChar(char c) {
        return Character.isLetterOrDigit(c)
                || c == '_' || c == '-' || c == '$';
    }

    /** Расширенный Implode: всегда возвращает символ (без проверки формата). */
    private static Expr<Term> implodeExt(Runtime rt, Expr<Term> args) {
        String text = termsToText(args);
        return text.isEmpty() ? Expr.empty() : Expr.singleton(new Sym(text));
    }

    private static boolean isIdentifier(String s) {
        if (s.isEmpty() || !Character.isLetter(s.charAt(0))) {
            return false;
        }
        for (int i = 1; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!Character.isLetterOrDigit(c) && c != '_' && c != '-') {
                return false;
            }
        }
        return true;
    }

    /** Список имён всех зарегистрированных встроенных функций. */
    // Стандартный набор встроенных Рефала-5 в формате (number name type),
    // совместимый с refgo / Refal-5 PZ.
    // '+'/'-'/'*'/'/''%'/'?' намеренно исключены: R5FW-Parser хардкодит их сам.
    private static final Object[][] STANDARD_BUILTINS = {
        { 1,  "Mu",           "special"  },
        { 2,  "Add",          "regular"  },
        { 3,  "Arg",          "regular"  },
        { 5,  "Card",         "regular"  },
        { 6,  "Chr",          "regular"  },
        { 10, "Div",          "regular"  },
        { 11, "Divmod",       "regular"  },
        { 12, "Explode",      "regular"  },
        { 13, "First",        "regular"  },
        { 14, "Get",          "regular"  },
        { 15, "Implode",      "regular"  },
        { 16, "Last",         "regular"  },
        { 17, "Lenw",         "regular"  },
        { 18, "Lower",        "regular"  },
        { 19, "Mod",          "regular"  },
        { 20, "Mul",          "regular"  },
        { 21, "Numb",         "regular"  },
        { 22, "Open",         "regular"  },
        { 23, "Ord",          "regular"  },
        { 24, "Print",        "regular"  },
        { 25, "Prout",        "regular"  },
        { 26, "Put",          "regular"  },
        { 27, "Putout",       "regular"  },
        { 29, "Step",         "regular"  },
        { 30, "Sub",          "regular"  },
        { 31, "Symb",         "regular"  },
        { 33, "Type",         "regular"  },
        { 34, "Upper",        "regular"  },
        { 35, "Sysfun",       "regular"  },
        { 50, "Residue",      "special"  },
        { 53, "Exit",         "regular"  },
        { 54, "Close",        "regular"  },
        { 58, "Implode_Ext",  "regular"  },
        { 59, "Explode_Ext",  "regular"  },
        { 60, "TimeElapsed",  "regular"  },
        { 61, "Compare",      "regular"  },
        { 66, "Write",        "regular"  },
        { 67, "ListOfBuiltin", "regular"  },
    };

    private static Expr<Term> listOfBuiltin(Runtime rt, Expr<Term> args) {
        Expr<Term> out = Expr.empty();
        for (Object[] row : STANDARD_BUILTINS) {
            int num = (int) row[0];
            String name = (String) row[1];
            String type = (String) row[2];
            Expr<Term> triple = Expr.empty();
            triple = triple.pushBack(new Num(BigInteger.valueOf(num)));
            triple = triple.pushBack(new Sym(name));
            triple = triple.pushBack(new Sym(type));
            out = out.pushBack(new Br(triple));
        }
        return out;
    }

    /** N-й аргумент командной строки (или пусто, если индекс вне диапазона). */
    private static Expr<Term> arg(Runtime rt, Expr<Term> args) {
        Term t = singleArg("Arg", args);
        if (!(t instanceof Num n)) {
            throw new RefalException("Arg: expected integer index, got "
                    + AstFormatter.format(t));
        }
        int idx = n.value().intValue();
        String[] cli = rt.programArgs();
        if (idx < 0 || idx >= cli.length) {
            return Expr.empty();
        }
        // Возвращаем аргумент как последовательность односимвольных строк
        // (классический Рефал-5 трактует <Arg N> именно так — это совместимо
        // с шаблонами вида e.Source : e.Base '.' e.Ref).
        String s = cli[idx];
        Expr<Term> out = Expr.empty();
        for (int i = 0; i < s.length(); i++) {
            out = out.pushBack(new Str(String.valueOf(s.charAt(i))));
        }
        return out;
    }

    // --- файловый ввод-вывод ---

    /** Открывает файл: режим, номер канала, имя файла (опционально). */
    private static Expr<Term> open(Runtime rt, Expr<Term> args) {
        if (args.size() < 2) {
            throw new RefalException("Open: expected at least mode and channel");
        }
        List<Term> a = args.toList();
        String mode = termAsText(a.get(0)).toLowerCase(java.util.Locale.ROOT);
        // Бинарный флаг 'b' (как в "wb", "rb", "ab") отбрасываем —
        if (mode.endsWith("b") && mode.length() > 1) {
            mode = mode.substring(0, mode.length() - 1);
        }
        if (!(a.get(1) instanceof Num n)) {
            throw new RefalException("Open: channel must be integer");
        }
        String filename;
        if (a.size() >= 3) {
            filename = termsToText(Expr.fromList(a.subList(2, a.size())));
        } else {
            try {
                filename = java.nio.file.Files
                        .createTempFile("refal5j-ch" + n.value(), ".tmp")
                        .toString();
            } catch (java.io.IOException e) {
                throw new RefalException("Open: cannot create temp file: " + e.getMessage());
            }
        }
        rt.openFile(n.value().longValue(), mode, filename);
        return Expr.empty();
    }

    /** Закрывает файловый канал. */
    private static Expr<Term> close(Runtime rt, Expr<Term> args) {
        Term t = singleArg("Close", args);
        if (!(t instanceof Num n)) {
            throw new RefalException("Close: channel must be integer");
        }
        rt.closeFile(n.value().longValue());
        return Expr.empty();
    }

    /** Читает строку из файла или канала; при конце файла возвращает пусто. */
    private static Expr<Term> get(Runtime rt, Expr<Term> args) {
        // На конце файла Get возвращает число 0,
        // а прочитанная строка — последовательность односимвольных строк.
        if (args.isEmpty()) {
            String line = rt.readStdinLine();
            return line == null ? Expr.singleton(new Num(0)) : explodeString(line);
        }
        Term t = singleArg("Get", args);
        if (!(t instanceof Num n)) {
            throw new RefalException("Get: channel must be integer");
        }
        long ch = n.value().longValue();
        if (ch == 0) {
            String line = rt.readStdinLine();
            return line == null ? Expr.singleton(new Num(0)) : explodeString(line);
        }
        String line = rt.readFileLine(ch);
        return line == null ? Expr.singleton(new Num(0)) : explodeString(line);
    }

    /** Разбивает строку на последовательность односимвольных Str-термов. */
    private static Expr<Term> explodeString(String s) {
        Expr<Term> out = Expr.empty();
        for (int i = 0; i < s.length(); i++) {
            out = out.pushBack(new Str(String.valueOf(s.charAt(i))));
        }
        return out;
    }

    /** Записывает данные в файл с переводом строки; возвращает записанное выражение. */
    private static Expr<Term> put(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException("Put: missing channel");
        }
        PeekResult<Term> pr = args.separateFront();
        if (!(pr.term() instanceof Num n)) {
            throw new RefalException("Put: channel must be integer");
        }
        rt.writeFile(n.value().longValue(), printExpr(pr.rest()) + "\n");
        return pr.rest();
    }

    /** Записывает данные в файл без перевода строки. */
    private static Expr<Term> putoutChan(Runtime rt, Expr<Term> args) {
        if (args.isEmpty()) {
            throw new RefalException("Putout: missing channel");
        }
        PeekResult<Term> pr = args.separateFront();
        if (!(pr.term() instanceof Num n)) {
            throw new RefalException("Putout: channel must be integer");
        }
        rt.writeFile(n.value().longValue(), printExpr(pr.rest()));
        return pr.rest();
    }

    private static Expr<Term> sysfun(Runtime rt, Expr<Term> args) {
        throw new RefalException("Sysfun: not supported");
    }

    /** Время работы интерпретатора в секундах (строка).
     * <TimeElapsed 0> — сбрасывает таймер (возвращает пусто).
     * <TimeElapsed>   — возвращает прошедшее время строкой "%.2f". */
    private static Expr<Term> timeElapsed(Runtime rt, Expr<Term> args) {
        if (!args.isEmpty()) {
            PeekResult<Term> pr = args.separateFront();
            if (pr.term() instanceof Num n
                    && n.value().signum() == 0
                    && pr.rest().isEmpty()) {
                rt.resetStartNanos();
                return Expr.empty();
            }
        }
        double sec = rt.timeElapsedSeconds();
        return Expr.singleton(new Str(String.format(java.util.Locale.ROOT, "%.2f", sec)));
    }

    private static String termAsText(Term t) {
        return switch (t) {
            case Sym s -> s.name();
            case Str s -> s.value();
            case Num n -> n.value().toString();
            default -> AstFormatter.format(t);
        };
    }

    /**
     * Внутренний сигнал завершения программы Exit: пробрасывается сквозь стек редукции,
     * Runtime/Main преобразует его в код возврата процесса.
     */
    public static final class ExitSignal extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final int code;

        public ExitSignal(int code) {
            super("Exit(" + code + ")");
            this.code = code;
        }

        public int code() {
            return code;
        }
    }
}
