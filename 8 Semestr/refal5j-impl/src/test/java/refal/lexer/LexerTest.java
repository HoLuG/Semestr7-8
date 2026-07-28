package refal.lexer;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LexerTest {

    @Test
    void emptySourceProducesOnlyEof() {
        List<Token> ts = Lexer.tokenize("");
        assertThat(ts).hasSize(1);
        assertThat(ts.get(0).type()).isEqualTo(TokenType.EOF);
        assertThat(ts.get(0).line()).isEqualTo(1);
        assertThat(ts.get(0).col()).isEqualTo(1);
    }

    @Test
    void recognizesAllPunctuation() {
        List<Token> ts = Lexer.tokenize("{}()<>=;,");
        assertThat(ts.stream().map(Token::type)).containsExactly(
                TokenType.LBRACE, TokenType.RBRACE,
                TokenType.LPAREN, TokenType.RPAREN,
                TokenType.LANGLE, TokenType.RANGLE,
                TokenType.EQUALS, TokenType.SEMI, TokenType.COMMA,
                TokenType.EOF);
    }

    @Test
    void recognizesEntryAndExtern() {
        List<Token> ts = Lexer.tokenize("$ENTRY Main; $EXTERN F, G;");
        assertThat(ts.stream().map(Token::type).toList()).startsWith(
                TokenType.ENTRY, TokenType.IDENT, TokenType.SEMI,
                TokenType.EXTERN, TokenType.IDENT, TokenType.COMMA,
                TokenType.IDENT, TokenType.SEMI);
    }

    @Test
    void integerWithMinusSign() {
        List<Token> ts = Lexer.tokenize("12 -5");
        assertThat(ts.get(0)).isEqualTo(new Token(TokenType.INT, "12", 1, 1));
        assertThat(ts.get(1)).isEqualTo(new Token(TokenType.INT, "-5", 1, 4));
    }

    @Test
    void singleQuotedStringWithoutEscapes() {
        // Одинарные кавычки в классическом Рефале-5 — последовательность
        // односимвольных строк, а не одна строка целиком.
        List<Token> ts = Lexer.tokenize("'hello'");
        assertThat(ts).hasSize(6); // 5 символов + EOF
        assertThat(ts.get(0).value()).isEqualTo("h");
        assertThat(ts.get(1).value()).isEqualTo("e");
        assertThat(ts.get(2).value()).isEqualTo("l");
        assertThat(ts.get(3).value()).isEqualTo("l");
        assertThat(ts.get(4).value()).isEqualTo("o");
    }

    @Test
    void doubleQuotedStringTokenizes() {
        List<Token> ts = Lexer.tokenize("\"abc\"");
        assertThat(ts.get(0).value()).isEqualTo("abc");
    }

    @Test
    void identifierWithDotsAndHyphens() {
        List<Token> ts = Lexer.tokenize("e.X my-name $foo");
        assertThat(ts.get(0).value()).isEqualTo("e.X");
        assertThat(ts.get(1).value()).isEqualTo("my-name");
        assertThat(ts.get(2).value()).isEqualTo("$foo");
    }

    @Test
    void lineCommentSkipped() {
        List<Token> ts = Lexer.tokenize("* this is a comment\nA");
        assertThat(ts).hasSize(2);
        assertThat(ts.get(0).type()).isEqualTo(TokenType.IDENT);
        assertThat(ts.get(0).value()).isEqualTo("A");
        assertThat(ts.get(0).line()).isEqualTo(2);
        assertThat(ts.get(0).col()).isEqualTo(1);
    }

    @Test
    void linesAndColsTrackedCorrectly() {
        List<Token> ts = Lexer.tokenize("A\n  B");
        assertThat(ts.get(0).line()).isEqualTo(1);
        assertThat(ts.get(0).col()).isEqualTo(1);
        assertThat(ts.get(1).line()).isEqualTo(2);
        assertThat(ts.get(1).col()).isEqualTo(3);
    }

    @Test
    void unterminatedStringRaises() {
        assertThatThrownBy(() -> Lexer.tokenize("'oops"))
                .isInstanceOf(LexException.class)
                .hasMessageContaining("Unterminated");
    }

    @Test
    void unexpectedCharRaises() {
        assertThatThrownBy(() -> Lexer.tokenize("@"))
                .isInstanceOf(LexException.class)
                .hasMessageContaining("Unexpected");
    }

    @Test
    void completeSamplePogram() {
        String src = """
                $ENTRY Main;
                Main { = 'hello'; }
                """;
        List<Token> ts = Lexer.tokenize(src);
        assertThat(ts.stream().map(Token::type).toList()).containsExactly(
                TokenType.ENTRY, TokenType.IDENT, TokenType.SEMI,
                TokenType.IDENT, TokenType.LBRACE,
                TokenType.EQUALS,
                // 'hello' → 5 односимвольных STRING-токенов
                TokenType.STRING, TokenType.STRING, TokenType.STRING,
                TokenType.STRING, TokenType.STRING,
                TokenType.SEMI,
                TokenType.RBRACE, TokenType.EOF);
    }
}
