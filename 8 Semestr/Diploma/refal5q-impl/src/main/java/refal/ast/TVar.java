package refal.ast;

import java.util.Objects;

/** t-переменная: один произвольный терм (включая скобочный). */
public record TVar(String name) implements Var {
    public TVar {
        Objects.requireNonNull(name, "TVar.name");
        if (name.isEmpty()) {
            throw new IllegalArgumentException("TVar.name must not be empty");
        }
    }

    @Override
    public char kind() {
        return 't';
    }
}
