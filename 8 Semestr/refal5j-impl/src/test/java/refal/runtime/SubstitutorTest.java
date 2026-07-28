package refal.runtime;

import org.junit.jupiter.api.Test;
import refal.ast.Br;
import refal.ast.Call;
import refal.ast.EVar;
import refal.ast.SVar;
import refal.ast.Sym;
import refal.ast.Term;
import refal.deque.Expr;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SubstitutorTest {

    @Test
    void substitutesAtomsUnchanged() {
        var out = Substitutor.substitute(
                List.of(new Sym("A"), new Sym("B")),
                Bindings.empty());
        assertThat(out.toList()).containsExactly(new Sym("A"), new Sym("B"));
    }

    @Test
    void substitutesEVariableAsConcat() {
        var env = Bindings.empty().with("e.X",
                List.of(new Sym("A"), new Sym("B"), new Sym("C")));
        var out = Substitutor.substitute(
                List.of(new EVar("X")), env);
        assertThat(out.toList()).containsExactly(
                new Sym("A"), new Sym("B"), new Sym("C"));
    }

    @Test
    void substitutesSurroundsEVariable() {
        var env = Bindings.empty().with("e.X",
                List.of(new Sym("B"), new Sym("C")));
        var out = Substitutor.substitute(
                List.of(new Sym("L"), new EVar("X"), new Sym("R")), env);
        assertThat(out.toList()).containsExactly(
                new Sym("L"), new Sym("B"), new Sym("C"), new Sym("R"));
    }

    @Test
    void substitutesInsideBrackets() {
        var env = Bindings.empty().with("s.X", List.of(new Sym("XX")));
        var out = Substitutor.substitute(
                List.of(new Br(Expr.fromList(List.of(new SVar("X"), new Sym("Y"))))),
                env);
        assertThat(out.toList()).containsExactly(
                new Br(Expr.fromList(List.of(new Sym("XX"), new Sym("Y")))));
    }

    @Test
    void substitutesInsideCall() {
        var env = Bindings.empty().with("e.X",
                List.of(new Sym("A"), new Sym("B")));
        var out = Substitutor.substitute(
                List.of(new Call("F", Expr.fromList(List.of(new EVar("X"))))), env);
        assertThat(out.toList()).containsExactly(
                new Call("F", Expr.fromList(List.of(new Sym("A"), new Sym("B")))));
    }

    @Test
    void unboundVariableIsAnError() {
        assertThatThrownBy(() -> Substitutor.substitute(
                List.of(new EVar("X")), Bindings.empty()))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void largeSubstitutionUsesConcat() {
        // Стресс: e.Big с 200 элементами — Expr.concat должен сработать без
        // деградации.
        var bigList = new java.util.ArrayList<Term>();
        for (int i = 0; i < 200; i++) {
            bigList.add(new Sym("X" + i));
        }
        var env = Bindings.empty().with("e.Big", bigList);
        var out = Substitutor.substitute(
                List.of(new Sym("L"), new EVar("Big"), new Sym("R")), env);
        assertThat(out.size()).isEqualTo(202);
        assertThat(out.toList().get(0)).isEqualTo(new Sym("L"));
        assertThat(out.toList().get(201)).isEqualTo(new Sym("R"));
    }
}
