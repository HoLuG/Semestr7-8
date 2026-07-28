package refal.lexer;

import java.util.Objects;

// Токен с координатами в исходнике (строка/колонка начиная с 1).
public record Token(TokenType type, String value, int line, int col) {
    public Token {
        Objects.requireNonNull(type, "Token.type");
        Objects.requireNonNull(value, "Token.value");
        if (line < 1) {
            throw new IllegalArgumentException("Token.line must be >= 1");
        }
        if (col < 1) {
            throw new IllegalArgumentException("Token.col must be >= 1");
        }
    }
}
