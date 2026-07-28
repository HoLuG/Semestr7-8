package refal.ast;

import java.util.Objects;

/** e-переменная: последовательность термов произвольной длины (≥0). */
public record EVar(String name) implements Var {
    public EVar {
        Objects.requireNonNull(name, "EVar.name");
        if (name.isEmpty()) {
            throw new IllegalArgumentException("EVar.name must not be empty");
        }
    }

    @Override
    public char kind() {
        return 'e';
    }
}
