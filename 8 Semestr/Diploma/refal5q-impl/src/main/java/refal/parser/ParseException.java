package refal.parser;

// Синтаксическая ошибка с указанием места.
public class ParseException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final int line;
    private final int col;

    public ParseException(String message, int line, int col) {
        super(line + ":" + col + ": " + message);
        this.line = line;
        this.col = col;
    }

    public int line() {
        return line;
    }

    public int col() {
        return col;
    }
}
