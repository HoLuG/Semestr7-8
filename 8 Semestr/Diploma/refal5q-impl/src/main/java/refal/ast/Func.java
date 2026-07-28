package refal.ast;

import java.util.List;
import java.util.Objects;

// Определение функции: имя и непустой список правил.
public record Func(String name, List<Rule> rules) {
    public Func {
        Objects.requireNonNull(name, "Func.name");
        if (name.isEmpty()) {
            throw new IllegalArgumentException("Func.name must not be empty");
        }
        Objects.requireNonNull(rules, "Func.rules");
        if (rules.isEmpty()) {
            throw new IllegalArgumentException(
                    "Func '" + name + "' must contain at least one rule");
        }
        rules = List.copyOf(rules);
    }
}
