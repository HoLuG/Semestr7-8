package refal.lexer;

import java.util.ArrayList;
import java.util.List;

// Лексер Рефала-5.
public final class Lexer {

    private final String src;
    private int i;
    private int line = 1;
    private int col = 1;
    // '*' трактуется как комментарий до конца строки только в начале строки;
    // в середине строки — это идентификатор-оператор умножения.
    private boolean atLineStart = true;

    public Lexer(String src) {
        this.src = src;
    }

    // Токенизировать строку; последний токен всегда EOF.
    public static List<Token> tokenize(String src) {
        return new Lexer(src).run();
    }

    private List<Token> run() {
        List<Token> out = new ArrayList<>();
        while (i < src.length()) {
            int startLine = line;
            int startCol = col;
            char c = src.charAt(i);

            if (c == '\n') {
                i++;
                line++;
                col = 1;
                atLineStart = true;
                continue;
            }
            if (Character.isWhitespace(c)) {
                advance();
                continue;
            }
            if (c == '*' && atLineStart) {
                skipLineComment();
                continue;
            }
            // Блочные комментарии в стиле C: /* ... */
            if (c == '/' && i + 1 < src.length() && src.charAt(i + 1) == '*') {
                skipBlockComment();
                continue;
            }
            // Строчные комментарии в стиле C: //...
            if (c == '/' && i + 1 < src.length() && src.charAt(i + 1) == '/') {
                skipLineComment();
                continue;
            }
            if (c == '\'' || c == '"') {
                readString(c, startLine, startCol, out);
                atLineStart = false;
                continue;
            }
            if (Character.isDigit(c) || (c == '-' && i + 1 < src.length()
                    && Character.isDigit(src.charAt(i + 1)))) {
                out.add(readInt(startLine, startCol));
                atLineStart = false;
                continue;
            }
            if (isIdentStart(c)) {
                out.add(readIdentLike(startLine, startCol));
                atLineStart = false;
                continue;
            }
            Token punct = readPunct(c, startLine, startCol);
            if (punct != null) {
                out.add(punct);
                atLineStart = false;
                continue;
            }
            // Односимвольные идентификаторы-операторы: +, -, *, /, %, ?
            // (используются в Рефале-5/refal-5-lambda как имена функций
            //  '+', '-', и т.д., а также в дополнительных встроенных)
            if (isOperatorIdent(c)) {
                out.add(new Token(TokenType.IDENT, String.valueOf(c), startLine, startCol));
                advance();
                atLineStart = false;
                continue;
            }
            throw new LexException(
                    "Unexpected character '" + c + "' (U+" + Integer.toHexString(c) + ")",
                    line, col);
        }
        out.add(new Token(TokenType.EOF, "", line, col));
        return out;
    }

    private void advance() {
        // Сюда попадает любой пробельный символ, кроме перевода строки;
        i++;
        col++;
    }

    private void skipLineComment() {
        while (i < src.length() && src.charAt(i) != '\n') {
            i++;
            col++;
        }
    }

    private void skipBlockComment() {
        // Пропускаем начальный «/*»
        i += 2;
        col += 2;
        while (i < src.length()) {
            char ch = src.charAt(i);
            if (ch == '*' && i + 1 < src.length() && src.charAt(i + 1) == '/') {
                i += 2;
                col += 2;
                return;
            }
            if (ch == '\n') {
                i++;
                line++;
                col = 1;
            } else {
                i++;
                col++;
            }
        }
        throw new LexException("Unterminated block comment", line, col);
    }

    // Читает строковый литерал в кавычках с обработкой escape-последовательностей.
    // Для одинарных кавычек ('abc') классический Рефал-5 трактует каждую букву
    // как отдельный односимвольный терм — поэтому в out добавляется по токену
    // STRING на каждый символ. Для двойных кавычек ("abc") — один STRING целиком.
    private void readString(char quote, int startLine, int startCol, List<Token> out) {
        int openLine = line;
        int openCol = col;
        advance();
        StringBuilder sb = new StringBuilder();
        // Запоминаем стартовые позиции каждого символа, чтобы выдавать
        // токены с правильными координатами при одинарной кавычке.
        List<int[]> charPositions = new ArrayList<>();
        while (i < src.length() && src.charAt(i) != quote) {
            int charLine = line;
            int charCol = col;
            char ch = src.charAt(i);
            if (ch == '\\') {
                int escLine = line;
                int escCol = col;
                advance();
                if (i >= src.length()) {
                    throw new LexException(
                            "Unterminated escape sequence", escLine, escCol);
                }
                char esc = src.charAt(i);
                char decoded;
                switch (esc) {
                    case 'n' -> decoded = '\n';
                    case 't' -> decoded = '\t';
                    case 'r' -> decoded = '\r';
                    case '\\' -> decoded = '\\';
                    case '\'' -> decoded = '\'';
                    case '"' -> decoded = '"';
                    case '<' -> decoded = '<';
                    case '>' -> decoded = '>';
                    case '(' -> decoded = '(';
                    case ')' -> decoded = ')';
                    case '0' -> decoded = '\0';
                    case 'x', 'X' -> {
                        advance();
                        if (i + 1 >= src.length()) {
                            throw new LexException(
                                    "Truncated \\x escape", escLine, escCol);
                        }
                        char h1 = src.charAt(i);
                        char h2 = src.charAt(i + 1);
                        int v1 = hexDigit(h1);
                        int v2 = hexDigit(h2);
                        if (v1 < 0 || v2 < 0) {
                            throw new LexException(
                                    "Bad \\x escape: \\x" + h1 + h2, escLine, escCol);
                        }
                        decoded = (char) (v1 * 16 + v2);
                        advance(); // h1
                        i++;
                        col++;     // h2
                        sb.append(decoded);
                        charPositions.add(new int[]{charLine, charCol});
                        continue;
                    }
                    default -> throw new LexException(
                            "Unknown escape sequence \\" + esc, escLine, escCol);
                }
                advance();
                sb.append(decoded);
                charPositions.add(new int[]{charLine, charCol});
            } else if (ch == '\n') {
                sb.append(ch);
                charPositions.add(new int[]{charLine, charCol});
                i++;
                line++;
                col = 1;
            } else {
                sb.append(ch);
                charPositions.add(new int[]{charLine, charCol});
                advance();
            }
        }
        if (i >= src.length()) {
            throw new LexException(
                    "Unterminated string literal (started at " + openLine + ":" + openCol + ")",
                    line, col);
        }
        advance(); // закрывающая кавычка
        if (quote == '\'') {
            // Каждый символ — отдельный односимвольный STRING-токен.
            String text = sb.toString();
            if (text.isEmpty()) {
                // Пустые одинарные кавычки не порождают ни одного терма;
                // вставляем один пустой STRING чтобы синтаксис не «съел» позицию.
                out.add(new Token(TokenType.STRING, "", startLine, startCol));
            } else {
                for (int k = 0; k < text.length(); k++) {
                    int[] pos = charPositions.get(k);
                    out.add(new Token(TokenType.STRING,
                            String.valueOf(text.charAt(k)), pos[0], pos[1]));
                }
            }
        } else {
            // Двойные кавычки — составной символ (Sym): "abc def" → один символ.
            // Соответствует семантике refgo и нужно для Implode/Implode_Ext.
            out.add(new Token(TokenType.QSYM, sb.toString(), startLine, startCol));
        }
    }

    private static int hexDigit(char c) {
        if (c >= '0' && c <= '9') {
            return c - '0';
        }
        if (c >= 'a' && c <= 'f') {
            return 10 + (c - 'a');
        }
        if (c >= 'A' && c <= 'F') {
            return 10 + (c - 'A');
        }
        return -1;
    }

    private Token readInt(int startLine, int startCol) {
        int j = i;
        if (src.charAt(j) == '-') {
            j++;
        }
        while (j < src.length() && Character.isDigit(src.charAt(j))) {
            j++;
        }
        String s = src.substring(i, j);
        col += s.length();
        i = j;
        return new Token(TokenType.INT, s, startLine, startCol);
    }

    private Token readIdentLike(int startLine, int startCol) {
        int j = i + 1;
        while (j < src.length() && isIdentCont(src.charAt(j))) {
            j++;
        }
        String s = src.substring(i, j);
        col += s.length();
        i = j;
        return switch (s) {
            case "$ENTRY" -> new Token(TokenType.ENTRY, s, startLine, startCol);
            case "$EXTERN" -> new Token(TokenType.EXTERN, s, startLine, startCol);
            default -> new Token(TokenType.IDENT, s, startLine, startCol);
        };
    }

    private Token readPunct(char c, int startLine, int startCol) {
        TokenType t = switch (c) {
            case '{' -> TokenType.LBRACE;
            case '}' -> TokenType.RBRACE;
            case '(' -> TokenType.LPAREN;
            case ')' -> TokenType.RPAREN;
            case '<' -> TokenType.LANGLE;
            case '>' -> TokenType.RANGLE;
            case '=' -> TokenType.EQUALS;
            case ';' -> TokenType.SEMI;
            case ',' -> TokenType.COMMA;
            default -> null;
        };
        if (t == null) {
            return null;
        }
        advance();
        return new Token(t, String.valueOf(c), startLine, startCol);
    }

    private static boolean isIdentStart(char c) {
        return Character.isLetter(c) || c == '_' || c == '.' || c == '$';
    }

    private static boolean isIdentCont(char c) {
        return Character.isLetterOrDigit(c) || c == '_' || c == '.' || c == '$' || c == '-';
    }

    private static boolean isOperatorIdent(char c) {
        return c == '+' || c == '-' || c == '*' || c == '/' || c == '%' || c == '?';
    }
}
