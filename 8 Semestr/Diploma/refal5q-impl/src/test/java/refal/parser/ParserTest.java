package refal.parser;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import refal.ast.AstFormatter;
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
import refal.support.Resources;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ParserTest {

    @Test
    void parsesEntryAndSimpleFunction() {
        Program p = Parser.parse("""
                $ENTRY Main;
                Main { = 'Hello'; }
                """);
        assertThat(p.entry()).hasValue("Main");
        Func f = p.getFunc("Main").orElseThrow();
        assertThat(f.rules()).hasSize(1);
        Rule r = f.rules().get(0);
        assertThat(r.pattern()).isEmpty();
        assertThat(r.result()).containsExactly(
                new Str("H"), new Str("e"), new Str("l"), new Str("l"), new Str("o"));
    }

    @Test
    void parsesEntryFunctionFormCombined() {
        Program p = Parser.parse("""
                $ENTRY Main { = A; }
                """);
        assertThat(p.entry()).hasValue("Main");
        assertThat(p.getFunc("Main")).isPresent();
    }

    @Test
    void parsesExternList() {
        Program p = Parser.parse("""
                $EXTERN Foo, Bar, Baz;
                Main { = Done; }
                """);
        assertThat(p.externs()).containsExactlyInAnyOrder("Foo", "Bar", "Baz");
    }

    @Test
    void parsesAllTermKindsInResult() {
        Program p = Parser.parse("""
                F { = 1 'a' s.X (B C) <G 1>; }
                """);
        Rule r = p.getFunc("F").orElseThrow().rules().get(0);
        assertThat(r.result()).containsExactly(
                new Num(1),
                new Str("a"),
                new SVar("X"),
                new Br(refal.deque.Expr.fromList(java.util.List.of(new Sym("B"), new Sym("C")))),
                new Call("G", refal.deque.Expr.fromList(java.util.List.of(new Num(1)))));
    }

    @Test
    void variablesAreRecognised() {
        Program p = Parser.parse("F { s.X t.Y e.Z = e.Z t.Y s.X; }");
        Rule r = p.getFunc("F").orElseThrow().rules().get(0);
        assertThat(r.pattern()).containsExactly(
                new SVar("X"),
                new TVar("Y"),
                new EVar("Z"));
        assertThat(AstFormatter.format(r.result()))
                .isEqualTo("e.Z t.Y s.X");
    }

    @Test
    void callInPatternIsRejected() {
        assertThatThrownBy(() -> Parser.parse("""
                F { <G s.X> = s.X; }
                """))
                .isInstanceOf(ParseException.class)
                .hasMessageContaining("Function call");
    }

    @Test
    void emptyVarIsRejected() {
        assertThatThrownBy(() -> Parser.parse("F { e. = ; }"))
                .isInstanceOf(ParseException.class)
                .hasMessageContaining("empty index");
    }

    @Test
    void emptyFunctionRejected() {
        assertThatThrownBy(() -> Parser.parse("F { }"))
                .isInstanceOf(ParseException.class)
                .hasMessageContaining("at least one rule");
    }

    @Test
    void unclosedBracketRejected() {
        assertThatThrownBy(() -> Parser.parse("F { = (A B C ; }"))
                .isInstanceOf(ParseException.class);
    }

    @Test
    void unclosedFunctionRejected() {
        assertThatThrownBy(() -> Parser.parse("F { = ;"))
                .isInstanceOf(ParseException.class);
    }

    @Test
    void noEqualsRejected() {
        assertThatThrownBy(() -> Parser.parse("F { s.X s.Y ; }"))
                .isInstanceOf(ParseException.class);
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "fixtures/bad-syntax/call-in-pattern.ref",
            "fixtures/bad-syntax/empty-function.ref",
            "fixtures/bad-syntax/empty-var.ref",
            "fixtures/bad-syntax/no-equals.ref",
            "fixtures/bad-syntax/unclosed-bracket.ref",
            "fixtures/bad-syntax/unclosed-function.ref",
            "fixtures/bad-syntax/unterminated-string.ref"
    })
    void allBadSyntaxFixturesAreRejected(String resource) {
        String src = Resources.read(resource);
        assertThatThrownBy(() -> Parser.parse(src))
                .isInstanceOfAny(ParseException.class,
                        refal.lexer.LexException.class);
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "fixtures/ok/hello.ref",
            "fixtures/ok/swap.ref",
            "fixtures/ok/calls.ref",
            "fixtures/ok/brackets.ref",
            "fixtures/ok/vars_ste.ref",
            "fixtures/ok/strings.ref",
            "fixtures/ok/recursion.ref",
            "fixtures/ok/repeated_var.ref",
            "fixtures/ok/arith.ref",
            "fixtures/ok/extern_noop.ref",
            "fixtures/desugared/reverse-out.ref",
            "fixtures/desugared/append-out.ref"
    })
    void okFixturesParseSuccessfully(String resource) {
        Program p = Parser.parse(Resources.read(resource));
        assertThat(p).isNotNull();
        assertThat(p.funcs()).isNotEmpty();
    }
}
