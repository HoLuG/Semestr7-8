package refal.ast;

// Переменная Рефала: s.X, t.X или e.X.
// Три конкретных типа: SVar, TVar, EVar — записи с полем name.
public sealed interface Var extends Term permits SVar, TVar, EVar {

    String name();

    char kind();

    // Строковое представление вида s.X, t.X, e.X.
    default String key() {
        return kind() + "." + name();
    }
}
