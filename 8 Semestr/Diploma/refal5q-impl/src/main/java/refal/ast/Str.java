package refal.ast;

import java.util.Objects;

// Строковый литерал '...'.
public record Str(String value) implements Term {
    public Str {
        Objects.requireNonNull(value, "Str.value");
    }
}
