package refal.lexer;

// Лексическая ошибка с указанием места в исходнике.
public class LexException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final int line;
    private final int col;

    public LexException(String message, int line, int col) {
        super(format(message, line, col));
        this.line = line;
        this.col = col;
    }

    public int line() {
        return line;
    }

    public int col() {
        return col;
    }

    private static String format(String message, int line, int col) {
        return line + ":" + col + ": " + message;
    }
}
