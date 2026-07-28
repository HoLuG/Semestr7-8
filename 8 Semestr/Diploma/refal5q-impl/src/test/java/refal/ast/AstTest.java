package refal.ast;

import org.junit.jupiter.api.Test;

import refal.deque.Expr;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class AstTest {

    @Test
    void symRejectsEmptyName() {
        assertThatThrownBy(() -> new Sym(""))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void varRejectsEmptyName() {
        assertThatThrownBy(() -> new SVar(""))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new TVar(""))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new EVar(""))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void varKeyMatchesCanonicalForm() {
        assertThat(new EVar("Rest").key()).isEqualTo("e.Rest");
        assertThat(new SVar("X").key()).isEqualTo("s.X");
        assertThat(new TVar("Y").key()).isEqualTo("t.Y");
    }

    @Test
    void brHoldsCorrectItems() {
        var br = new Br(Expr.fromList(List.of(new Sym("A"))));
        assertThat(br.items().size()).isEqualTo(1);
        assertThat(br.items().iterator().next()).isEqualTo(new Sym("A"));
    }

    @Test
    void funcRequiresAtLeastOneRule() {
        assertThatThrownBy(() -> new Func("F", List.of()))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void programBuilderPreservesInsertionOrder() {
        var f1 = new Func("F", List.of(new Rule(List.of(), List.of())));
        var f2 = new Func("G", List.of(new Rule(List.of(), List.of())));
        var prog = Program.builder().addFunc(f1).addFunc(f2).entry("F").build();
        assertThat(prog.funcs().keySet()).containsExactly("F", "G");
        assertThat(prog.entry()).hasValue("F");
    }

    @Test
    void astFormatterRoundtripExamples() {
        var sym = new Sym("Hello");
        assertThat(AstFormatter.format(sym)).isEqualTo("Hello");

        var list = List.<Term>of(
                new Sym("A"),
                new Num(42L),
                new Str("xy"),
                new EVar("X"),
                new Br(Expr.fromList(List.of(new Sym("B"), new Sym("C")))),
                new Call("F", Expr.fromList(List.of(new Sym("A")))));
        assertThat(AstFormatter.format(list))
                .isEqualTo("A 42 'xy' e.X (B C) <F A>");
    }
}
