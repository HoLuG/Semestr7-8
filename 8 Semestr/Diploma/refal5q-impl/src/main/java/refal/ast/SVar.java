package refal.ast;

import java.util.Objects;

/** s-переменная: один атомарный (нескобочный) терм. */
public record SVar(String name) implements Var {
    public SVar {
        Objects.requireNonNull(name, "SVar.name");
        if (name.isEmpty()) {
            throw new IllegalArgumentException("SVar.name must not be empty");
        }
    }

    @Override
    public char kind() {
        return 's';
    }
}
