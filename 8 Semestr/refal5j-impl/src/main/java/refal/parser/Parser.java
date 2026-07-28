package refal.parser;

import refal.ast.Br;
import refal.ast.Call;
import refal.ast.Func;
import refal.ast.Num;
import refal.ast.Program;
import refal.ast.Rule;
import refal.ast.Str;
import refal.ast.Sym;
import refal.ast.Term;
import refal.ast.SVar;
import refal.ast.TVar;
import refal.ast.EVar;
import refal.lexer.Lexer;
import refal.lexer.Token;
import refal.lexer.TokenType;

import refal.deque.Expr;

import java.util.ArrayList;
import java.util.List;

/*
 * Рекурсивно-нисходящий парсер базисного подмножества Рефала-5.
 *
 * Program      ::= TopLevel* EOF
 * TopLevel     ::= EntryDecl | ExternDecl | FuncDef
 * EntryDecl    ::= "$ENTRY" Ident ";" | "$ENTRY" Ident "{" Rule+ "}"
 * ExternDecl   ::= "$EXTERN" Ident ("," Ident)* ";"
 * FuncDef      ::= Ident "{" Rule+ "}"
 * Rule         ::= Pattern "=" Result ";"?
 *
 * Pattern      ::= PatternTerm*
 * PatternTerm  ::= Int | Str | QuotedSym | "(" PatternTerm* ")" | Var
 *
 * Result       ::= ResultTerm*
 * ResultTerm   ::= Int | Str | QuotedSym | "(" ResultTerm* ")"
 *                | "<" Ident ResultTerm* ">"
 *                | Var | Ident
 *
 * Var          ::= ("s" | "t" | "e") "." VarName
 * VarName      ::= (Letter | Digit | "_" | "." | "$")+
 * Ident        ::= Letter (Letter | Digit | "_" | "-" | "+" | ".")*
 * Int          ::= Digit+
 * Str          ::= '"' Char* '"'   -- строка становится последовательностью символов
 * QuotedSym    ::= "'" Char* "'"   -- quoted symbol (один атом)
 *
 * s. — символьная переменная (один атом), t. — термовая (один терм),
 * e. — выражение-переменная (любая последовательность термов).
 * В Pattern вызовы функций "<...>" недопустимы.
 */
public final class Parser {

    private final List<Token> tokens;
    private int i;

    public Parser(List<Token> tokens) {
        this.tokens = tokens;
    }

    public static Program parse(String src) {
        return new Parser(Lexer.tokenize(src)).parseProgram();
    }

    // Распарсить последовательность термов (используется в CLI и тестах).
    public static List<Term> parseTerms(String src) {
        Parser p = new Parser(Lexer.tokenize(src));
        List<Term> items = new ArrayList<>();
        while (p.peek().type() != TokenType.EOF) {
            items.add(p.parseResultTerm());
        }
        return items;
    }

    public Program parseProgram() {
        Program.Builder b = Program.builder();
        while (peek().type() != TokenType.EOF) {
            Token t = peek();
            switch (t.type()) {
                case ENTRY -> parseEntry(b);
                case EXTERN -> parseExtern(b);
                case IDENT -> parseTopLevelFunc(b);
                default -> throw err(t, "Unexpected token at top level: " + t.type());
            }
        }
        return b.build();
    }

    private void parseEntry(Program.Builder b) {
        Token kw = expect(TokenType.ENTRY);
        Token name = expect(TokenType.IDENT);
        if (peek().type() == TokenType.LBRACE) {
            // '$ENTRY Name { ... }' — определяет функцию и помечает её как точку входа.
            Func f = parseFuncBody(name.value());
            b.addFunc(f);
            b.entry(name.value());
        } else {
            expect(TokenType.SEMI);
            // Если уже была объявлена другая точка входа — последняя выигрывает; это
            // согласовано с поведением Python-прототипа.
            b.entry(name.value());
            // Подавляем предупреждение «неиспользуемое ключевое слово» — просто маркер.
            if (kw == null) {
                throw new IllegalStateException();
            }
        }
    }

    private void parseExtern(Program.Builder b) {
        expect(TokenType.EXTERN);
        List<String> names = new ArrayList<>();
        names.add(expect(TokenType.IDENT).value());
        while (peek().type() == TokenType.COMMA) {
            i++;
            names.add(expect(TokenType.IDENT).value());
        }
        expect(TokenType.SEMI);
        b.addExterns(names);
    }

    private void parseTopLevelFunc(Program.Builder b) {
        Token name = expect(TokenType.IDENT);
        if (name.value().startsWith("__")) {
            throw err(name, "Function name '" + name.value()
                    + "' must not start with double underscore");
        }
        Func f = parseFuncBody(name.value());
        b.addFunc(f);
    }

    private Func parseFuncBody(String name) {
        Token lb = expect(TokenType.LBRACE);
        List<Rule> rules = new ArrayList<>();
        while (peek().type() != TokenType.RBRACE) {
            if (peek().type() == TokenType.EOF) {
                throw err(peek(), "Unclosed '{' for function '" + name + "' (opened at "
                        + lb.line() + ":" + lb.col() + ")");
            }
            rules.add(parseRule());
        }
        expect(TokenType.RBRACE);
        if (rules.isEmpty()) {
            throw err(lb, "Function '" + name + "' must contain at least one rule");
        }
        return new Func(name, rules);
    }

    private Rule parseRule() {
        List<Term> pattern = parseUntilEqualsAsPattern();
        expect(TokenType.EQUALS);
        List<Term> result = parseUntilSemiAsResult();
        // ';' между правилами обязательна, но перед '}' закрывающим функцию
        // её можно опускать (расширение, совместимое с refal-5-lambda).
        if (peek().type() == TokenType.SEMI) {
            i++;
        }
        return new Rule(pattern, result);
    }

    private List<Term> parseUntilEqualsAsPattern() {
        List<Term> out = new ArrayList<>();
        while (true) {
            Token t = peek();
            switch (t.type()) {
                case EQUALS -> {
                    return out;
                }
                case EOF, RBRACE, SEMI -> throw err(
                        t, "Unexpected " + t.type() + ", expected '=' to end pattern");
                default -> out.add(parsePatternTerm());
            }
        }
    }

    private List<Term> parseUntilSemiAsResult() {
        List<Term> out = new ArrayList<>();
        while (true) {
            Token t = peek();
            switch (t.type()) {
                case SEMI, RBRACE -> {
                    // RBRACE (закрывающая «}») — последнее правило, «;» опционально перед «}».
                    return out;
                }
                case EOF -> throw err(
                        t, "Unexpected " + t.type() + ", expected ';' to end rule");
                default -> out.add(parseResultTerm());
            }
        }
    }

    private Term parsePatternTerm() {
        Token t = peek();
        return switch (t.type()) {
            case INT -> {
                i++;
                yield new Num(new java.math.BigInteger(t.value()));
            }
            case STRING -> {
                i++;
                yield new Str(t.value());
            }
            case QSYM -> {
                i++;
                // Пустой "" эквивалентен пустому выражению — для уникальности
                // используем Str с пустой строкой? Лучше: считаем "" служебным
                // маркером пустого Sym → возвращаем Str("") (всё равно потом отбросится).
                yield t.value().isEmpty() ? new Str("") : new Sym(t.value());
            }
            case LPAREN -> {
                Token open = t;
                i++;
                List<Term> inner = new ArrayList<>();
                while (peek().type() != TokenType.RPAREN) {
                    if (peek().type() == TokenType.EOF) {
                        throw err(open, "Unclosed '(' in pattern");
                    }
                    inner.add(parsePatternTerm());
                }
                expect(TokenType.RPAREN);
                yield new Br(Expr.fromList(inner));
            }
            case LANGLE -> throw err(t,
                    "Function call '<...>' is not allowed in pattern");
            case IDENT -> {
                i++;
                yield identToTerm(t);
            }
            default -> throw err(t, "Unexpected token in pattern: " + t.type());
        };
    }

    Term parseResultTerm() {
        Token t = peek();
        return switch (t.type()) {
            case INT -> {
                i++;
                yield new Num(new java.math.BigInteger(t.value()));
            }
            case STRING -> {
                i++;
                yield new Str(t.value());
            }
            case QSYM -> {
                i++;
                yield t.value().isEmpty() ? new Str("") : new Sym(t.value());
            }
            case LPAREN -> {
                Token open = t;
                i++;
                List<Term> inner = new ArrayList<>();
                while (peek().type() != TokenType.RPAREN) {
                    if (peek().type() == TokenType.EOF) {
                        throw err(open, "Unclosed '(' in result");
                    }
                    inner.add(parseResultTerm());
                }
                expect(TokenType.RPAREN);
                yield new Br(Expr.fromList(inner));
            }
            case LANGLE -> {
                Token open = t;
                i++;
                Token head = peek();
                if (head.type() != TokenType.IDENT) {
                    throw err(head, "Expected function name after '<', got " + head.type());
                }
                i++;
                List<Term> args = new ArrayList<>();
                while (peek().type() != TokenType.RANGLE) {
                    if (peek().type() == TokenType.EOF) {
                        throw err(open, "Unclosed '<' in call");
                    }
                    args.add(parseResultTerm());
                }
                expect(TokenType.RANGLE);
                yield new Call(head.value(), Expr.fromList(args));
            }
            case IDENT -> {
                i++;
                yield identToTerm(t);
            }
            default -> throw err(t, "Unexpected token in result: " + t.type());
        };
    }

    // Идентификатор как терм: если начинается с s./t./e. — это переменная, иначе символ.
    private Term identToTerm(Token t) {
        String s = t.value();
        if (s.length() >= 2 && s.charAt(1) == '.'
                && (s.charAt(0) == 's' || s.charAt(0) == 't' || s.charAt(0) == 'e')) {
            String name = s.substring(2);
            if (name.isEmpty()) {
                throw err(t, "Variable '" + s + "' has empty index");
            }
            char first = name.charAt(0);
            if (!Character.isLetterOrDigit(first) && first != '_' && first != '.' && first != '$') {
                throw err(t, "Invalid variable name '" + s
                        + "': index must start with letter, digit, '_', '.' or '$'");
            }
            return switch (s.charAt(0)) {
                case 's' -> new SVar(name);
                case 't' -> new TVar(name);
                case 'e' -> new EVar(name);
                default -> throw err(t, "Unknown variable kind: '" + s.charAt(0) + "'");
            };
        }
        return new Sym(s);
    }

    // --- вспомогательные методы для токенов ---

    private Token peek() {
        return tokens.get(i);
    }

    private Token expect(TokenType type) {
        Token t = peek();
        if (t.type() != type) {
            throw err(t, "Expected " + type + ", got " + t.type() + " ('" + t.value() + "')");
        }
        i++;
        return t;
    }

    private static ParseException err(Token at, String message) {
        return new ParseException(message, at.line(), at.col());
    }
}
