package refal.ast;

import java.util.Objects;

// Символьный идентификатор: Cons, A и т.п.
public record Sym(String name) implements Term {
    public Sym {
        Objects.requireNonNull(name, "Sym.name");
        if (name.isEmpty()) {
            throw new IllegalArgumentException("Sym.name must not be empty");
        }
    }
}
