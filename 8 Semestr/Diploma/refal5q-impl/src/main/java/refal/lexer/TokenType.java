package refal.lexer;

/** Виды токенов языка Рефала-5 (базовое подмножество). */
public enum TokenType {
    LBRACE,
    RBRACE,
    LPAREN,
    RPAREN,
    LANGLE,
    RANGLE,
    EQUALS,
    SEMI,
    COMMA,
    INT,
    STRING,
    QSYM,
    IDENT,
    ENTRY,
    EXTERN,
    EOF
}
