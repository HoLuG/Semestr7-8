package refal.semantic;

// Семантическая ошибка с указанием контекста (имя функции, индекс правила).
public class SemanticException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final String funcName;
    private final int ruleIndex;
    private final Kind kind;

    // Вид ошибки — чтобы тесты могли различать их без разбора текста сообщения.
    public enum Kind {
        DUPLICATE_FUNCTION,
        UNDEFINED_FUNCTION,
        UNDEFINED_ENTRY,
        UNBOUND_VARIABLE,
        VARIABLE_TYPE_MISMATCH,
        CALL_IN_PATTERN,
        BUILTIN_SHADOW
    }

    public SemanticException(Kind kind, String message, String funcName, int ruleIndex) {
        super(message);
        this.kind = kind;
        this.funcName = funcName;
        this.ruleIndex = ruleIndex;
    }

    public Kind kind() {
        return kind;
    }

    public String funcName() {
        return funcName;
    }

    public int ruleIndex() {
        return ruleIndex;
    }
}
