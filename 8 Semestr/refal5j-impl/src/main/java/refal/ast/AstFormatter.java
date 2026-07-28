package refal.ast;

import java.util.List;

public final class AstFormatter {
    private AstFormatter() {
    }

    public static String format(Term t) {
        StringBuilder sb = new StringBuilder();
        appendTerm(sb, t);
        return sb.toString();
    }

    public static String format(List<Term> terms) {
        StringBuilder sb = new StringBuilder();
        appendList(sb, terms);
        return sb.toString();
    }

    private static void appendTerm(StringBuilder sb, Term t) {
        switch (t) {
            case Sym s -> sb.append(s.name());
            case Num n -> sb.append(n.value());
            case Str s -> sb.append('\'').append(s.value()).append('\'');
            case Var v -> sb.append(v.kind()).append('.').append(v.name());
            case Br b -> {
                sb.append('(');
                appendList(sb, b.items());
                sb.append(')');
            }
            case Call c -> {
                sb.append('<').append(c.fn());
                if (!c.args().isEmpty()) {
                    sb.append(' ');
                    appendList(sb, c.args());
                }
                sb.append('>');
            }
        }
    }

    private static void appendList(StringBuilder sb, Iterable<Term> ts) {
        boolean first = true;
        for (Term t : ts) {
            if (!first) {
                sb.append(' ');
            }
            first = false;
            appendTerm(sb, t);
        }
    }
}
