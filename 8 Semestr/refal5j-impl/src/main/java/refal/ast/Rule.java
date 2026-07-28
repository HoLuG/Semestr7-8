package refal.ast;

import java.util.List;
import java.util.Objects;

// Правило функции: Pattern = Result;
public record Rule(List<Term> pattern, List<Term> result) {
    public Rule {
        Objects.requireNonNull(pattern, "Rule.pattern");
        Objects.requireNonNull(result, "Rule.result");
        pattern = List.copyOf(pattern);
        result = List.copyOf(result);
    }
}
